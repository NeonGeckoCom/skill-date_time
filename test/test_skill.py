# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import datetime
import shutil
import unittest
import pytest
import datetime as dt


from neon_utils.skills.neon_skill import LOG
from os import mkdir
from os.path import dirname, join, exists
from pytz import timezone
from mock import Mock
from ovos_bus_client import Message
from ovos_utils.messagebus import FakeBus


class TestSkill(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        from mycroft.skills.skill_loader import SkillLoader

        bus = FakeBus()
        bus.run_in_thread()
        skill_loader = SkillLoader(bus, dirname(dirname(__file__)))
        skill_loader.load()
        cls.skill = skill_loader.instance
        cls.test_fs = join(dirname(__file__), "skill_fs")
        if not exists(cls.test_fs):
            mkdir(cls.test_fs)
        cls.skill.settings_write_path = cls.test_fs
        cls.skill.file_system.path = cls.test_fs

        # Override speak and speak_dialog to test passed arguments
        cls.skill.speak = Mock()
        cls.skill.speak_dialog = Mock()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.test_fs)

    def tearDown(self) -> None:
        self.skill.speak.reset_mock()
        self.skill.speak_dialog.reset_mock()

    def test_00_skill_init(self):
        # Test any parameters expected to be set in init or initialize methods
        from neon_utils.skills import NeonSkill

        self.assertIsInstance(self.skill, NeonSkill)

    def test_handle_idle(self):
        class MockGui:
            def __init__(self):
                self._data = dict()
                self.show_page = Mock()

            def __setitem__(self, key, value):
                self._data[key] = value

            def __getitem__(self, item):
                return self._data[item]

            @staticmethod
            def clear():
                pass

        real_gui = self.skill.gui
        mock_gui = MockGui()
        self.skill.gui = mock_gui

        self.skill.handle_idle(Message("test"))
        self.assertIsInstance(mock_gui["time_string"], str)
        self.assertEqual(mock_gui["ampm_string"], '')
        self.assertIsInstance(mock_gui["date_string"], str)
        self.assertIsInstance(mock_gui["weekday_string"], str)
        self.assertIsInstance(mock_gui["month_string"], str)
        self.assertIsInstance(mock_gui["year_string"], str)
        self.skill.gui.show_page.assert_called_once()
        self.skill.gui.show_page.assert_called_with("idle.qml")

        self.skill.gui = real_gui

    def test_get_display_date(self):
        from neon_utils.user_utils import get_default_user_config
        config = get_default_user_config()
        config['user']['username'] = 'test_user'
        config['units']['date'] = "MDY"
        test_message = Message("test", {}, {"username": "test_user",
                                            "user_profiles": [config]})

        test_date = dt.datetime(month=1, day=2, year=2000)

        date_str = self.skill.get_display_date(test_date, message=test_message)
        self.assertEqual(date_str, "1/2/2000")

        config['units']['date'] = "DMY"
        test_message = Message("test", {}, {"username": "test_user",
                                            "user_profiles": [config]})
        date_str = self.skill.get_display_date(test_date, message=test_message)
        self.assertEqual(date_str, "2/1/2000")

        config['units']['date'] = "YMD"
        test_message = Message("test", {}, {"username": "test_user",
                                            "user_profiles": [config]})
        date_str = self.skill.get_display_date(test_date, message=test_message)
        self.assertEqual(date_str, "2000/1/2")

        now_date_str = self.skill.get_display_date()
        self.assertNotEqual(date_str, now_date_str)

    def test_get_display_current_time(self):
        from neon_utils.user_utils import get_default_user_config
        config = get_default_user_config()
        config['user']['username'] = 'test_user'

        # Default behavior
        current_time = self.skill.get_display_current_time()
        self.assertIsInstance(current_time, str)
        self.assertEqual(len(current_time.split(':')), 2)

        # Specify location
        current_time_honolulu = self.skill.get_display_current_time("honolulu")
        self.assertIsInstance(current_time_honolulu, str)
        self.assertEqual(len(current_time_honolulu.split(':')), 2)
        self.assertIn('m', current_time_honolulu.lower())
        self.assertNotEqual(current_time, current_time_honolulu)

        config['units']['time'] = 24
        test_message = Message("test", {}, {"username": "test_user",
                                            "user_profiles": [config]})

        # Default location, specify time 24h
        dt_utc = dt.datetime.now(dt.timezone.utc).replace(hour=23, minute=30)
        utc_time = self.skill.get_display_current_time(dt_utc=dt_utc,
                                                       message=test_message)
        self.assertEqual(utc_time, "23:30")

        # Specify location, 24h
        az_time = self.skill.get_display_current_time("phoenix", dt_utc,
                                                      message=test_message)
        self.assertEqual(az_time, "16:30")

        self.skill.settings['use_ampm'] = True
        config['units']['time'] = 12

        # Default location with AM/PM
        test_message = Message("test", {}, {"username": "test_user",
                                            "user_profiles": [config]})
        utc_time = self.skill.get_display_current_time(dt_utc=dt_utc,
                                                       message=test_message)
        self.assertEqual(utc_time, "11:30 PM")

        # Specify location with AM/PM
        az_time = self.skill.get_display_current_time("phoenix", dt_utc,
                                                      message=test_message)
        self.assertEqual(az_time, "4:30 PM")

        self.skill.settings['use_ampm'] = False
        # Default location, no AM/PM
        utc_time = self.skill.get_display_current_time(dt_utc=dt_utc,
                                                       message=test_message)
        self.assertEqual(utc_time, "11:30")
        # Specify location, always shows AM/PM
        az_time = self.skill.get_display_current_time("phoenix", dt_utc,
                                                      message=test_message)
        self.assertEqual(az_time, "4:30 PM")

    def test_get_weekday(self):
        self.assertIsInstance(self.skill.get_weekday(), str)
        today = dt.datetime.now(dt.timezone.utc)
        tomorrow = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
        self.assertNotEqual(self.skill.get_weekday(today),
                            self.skill.get_weekday(tomorrow))
        self.assertEqual(self.skill.get_weekday(location="Seattle"),
                         self.skill.get_weekday(location="Portland"))

        known_day = dt.datetime(day=1, month=1, year=2000)
        self.assertEqual(self.skill.get_weekday(known_day), "Saturday")

    def test_get_month_date(self):
        from neon_utils.user_utils import get_default_user_config
        config = get_default_user_config()
        config['user']['username'] = 'test_user'
        test_date = dt.datetime(month=1, day=1, year=2000)

        config['units']['date'] = "MDY"
        test_message = Message("test", {}, {"username": "test_user",
                                            "user_profiles": [config]})
        date_str = self.skill.get_month_date(test_date, message=test_message)
        self.assertEqual(date_str, "January 01")

        config['units']['date'] = "DMY"
        test_message = Message("test", {}, {"username": "test_user",
                                            "user_profiles": [config]})
        date_str = self.skill.get_month_date(test_date, message=test_message)
        self.assertEqual(date_str, "01 January")

        config['units']['date'] = "YMD"
        test_message = Message("test", {}, {"username": "test_user",
                                            "user_profiles": [config]})
        date_str = self.skill.get_month_date(test_date, message=test_message)
        self.assertEqual(date_str, "January 01")

        now_date_str = self.skill.get_month_date()
        self.assertNotEqual(date_str, now_date_str)

    def test_get_year(self):
        self.assertIsInstance(self.skill.get_year(), str)
        date = datetime.datetime(month=1, day=1, year=2000)
        self.assertEqual(self.skill.get_year(date), "2000")
        self.assertEqual(self.skill.get_year(date, "Seattle"), "2000")
        self.assertIsInstance(self.skill.get_year(location="Seattle"), str)

    def test_get_next_leap_year(self):
        for year in (2000, 2001, 2002, 2003):
            self.assertEqual(self.skill.get_next_leap_year(year), 2004)
        self.assertEqual(self.skill.get_next_leap_year(2004), 2008)

    def test_is_leap_year(self):
        for year in (1999, 2001, 2002, 2003):
            self.assertFalse(self.skill.is_leap_year(year))
        for year in (2000, 2004, 2008):
            self.assertTrue(self.skill.is_leap_year(year))

    def test_handle_query_time(self):
        default_location_message = Message("test_message",
                                           {"utterance": "what time is it"})
        self.skill.handle_query_time(default_location_message)
        self.skill.speak_dialog.assert_called_once()
        call_args = self.skill.speak_dialog.call_args[0]
        self.assertEqual(call_args[0], "time.current")
        self.assertEqual(set(call_args[1].keys()), {"time"})

        spec_location_message = Message(
            "test_message", {"location": "london",
                             "utterance": "what time is it in london"})
        self.skill.handle_query_time(spec_location_message)
        call_args = self.skill.speak_dialog.call_args[0]
        self.assertEqual(call_args[0], "date_time_in_location")
        self.assertEqual(call_args[1]["location"], "London")
        self.assertEqual(set(call_args[1].keys()), {"location", "time"})

    def test_handle_query_date(self):
        default_location_message = Message("test_message",
                                           {"utterance": "what is the date"})
        self.skill.handle_query_date(default_location_message)
        self.skill.speak_dialog.assert_called_once()
        call_args = self.skill.speak_dialog.call_args[0]
        self.assertEqual(call_args[0], "date")
        self.assertEqual(set(call_args[1].keys()), {"date"})

    def test_handle_query_dow(self):
        default_location_message = Message(
            "test_message", {"utterance": "what is the day of the week"})
        self.skill.handle_query_dow(default_location_message)
        self.skill.speak_dialog.assert_called_once()
        call_args = self.skill.speak_dialog.call_args[0]
        self.assertEqual(call_args[0], "date")
        self.assertEqual(set(call_args[1].keys()), {"date"})

    def test_get_timezone(self):
        la_timezone = timezone("America/Los_Angeles")
        dict_test_cases = [
            {"city": "seattle"},
            {"city": "seattle", "state": "washington"},
            {"city": "seattle", "country": "united states"},
            # "pacific time",
            "los angeles time"
        ]
        for case in dict_test_cases:
            tz = self.skill.get_timezone(case)
            self.assertIsInstance(tz, dt.tzinfo)
            self.assertEqual(tz, la_timezone)
        str_test_cases = {
            "seattle": la_timezone,
            "seattle washington": la_timezone,
            "seattle, wa": la_timezone,
            "paris texas": timezone("America/Chicago")
        }
        for case in str_test_cases:
            self.assertEqual(self.skill.get_timezone(case),
                             str_test_cases[case])

    def test_get_local_datetime(self):
        # Test datetime, no location
        test_location = {"city": "Kirkland",
                         "state": "Washington",
                         "country": "USA",
                         "tz": "America/Los_Angeles"}
        test_message = Message("", context={"username": "test_user",
                                            "user_profiles": [{
                                                "user": {
                                                    "username": "test_user"},
                                                "location": test_location}
                                            ]})
        time_la = self.skill.get_local_datetime(None, test_message)
        self.assertAlmostEqual(time_la.timestamp(),
                               datetime.datetime.now(timezone(
                                   "America/Los_Angeles")).timestamp(), 0)

        test_location = {"city": "New York",
                         "state": "New York",
                         "country": "USA",
                         "tz": "America/New_York"}
        test_message = Message("", context={"username": "test_user",
                                            "user_profiles": [{
                                                "user": {
                                                    "username": "test_user"},
                                                "location": test_location}
                                            ]})
        time_ny = self.skill.get_local_datetime(None, test_message)
        self.assertAlmostEqual(time_ny.timestamp(),
                               datetime.datetime.now(timezone(
                                   "America/New_York")).timestamp(), 0)

        self.assertNotEqual(time_la.tzinfo, time_ny.tzinfo)

        # Test datetime with location
        time = self.skill.get_local_datetime("Chicago")
        self.assertAlmostEqual(time.timestamp(),
                               datetime.datetime.now(timezone(
                                   "America/Chicago")).timestamp(), 0)

        # Test datetime invalid location
        real_gettz = self.skill.get_timezone
        self.skill.get_timezone = Mock(return_value=None)
        self.skill.get_local_datetime("Not a real place")
        self.skill.get_timezone.assert_called_with("Not a real place")
        self.skill.speak_dialog.assert_called_once_with(
            "time.tz.not.found", {"location": "Not a real place"})
        self.skill.get_timezone = real_gettz

    def test_get_spoken_time(self):
        # Test no location
        test_location = {"city": "Kirkland",
                         "state": "Washington",
                         "country": "USA",
                         "tz": "America/Los_Angeles"}
        test_message = Message("", context={"username": "test_user",
                                            "user_profiles": [{
                                                "user": {
                                                    "username": "test_user"},
                                                "location": test_location}
                                            ]})
        # Skill specifies ampm, user default time format (12)
        self.skill.settings['use_ampm'] = True
        time = self.skill.get_spoken_time(message=test_message)
        self.assertIn('m', time)

        # Skill specifies ampm but user uses 24-hour time
        test_message.context['user_profiles'][0]['units'] = {"time": 24}
        time = self.skill.get_spoken_time(message=test_message)
        self.assertNotIn('m', time)

        # Skill specifies no ampm, user uses 12-hour time
        test_message.context['user_profiles'][0]['units'] = {"time": 12}
        self.skill.settings['use_ampm'] = False
        time = self.skill.get_spoken_time(message=test_message)
        self.assertNotIn('m', time)

        # Test with location, default 12-hour time
        time = self.skill.get_spoken_time("Seattle")
        self.assertIn('m', time)

        time = self.skill.get_spoken_time("Lawrence, Kansas")
        self.assertIn('m', time)

    def test_show_time_gui(self):
        real_gui = self.skill.gui.show_page
        self.skill.gui.show_page = Mock()

        # Default location, with AM/PM
        self.skill.show_time_gui(None, "12:30 PM", "Date")
        self.assertEqual(self.skill.gui['location'], "")
        self.assertEqual(self.skill.gui['hours'], "12")
        self.assertEqual(self.skill.gui['minutes'], "30")
        self.assertEqual(self.skill.gui['ampm'], "PM")
        self.assertEqual(self.skill.gui['date_string'], "Date")
        self.skill.gui.show_page.assert_called_with("time.qml")

        # Default location, no AM/PM
        self.skill.show_time_gui(None, "12:30", "Date")
        self.assertEqual(self.skill.gui['location'], "")
        self.assertEqual(self.skill.gui['hours'], "12")
        self.assertEqual(self.skill.gui['minutes'], "30")
        self.assertEqual(self.skill.gui['ampm'], "")
        self.assertEqual(self.skill.gui['date_string'], "Date")
        self.skill.gui.show_page.assert_called_with("time.qml")

        # With location
        self.skill.show_time_gui("seattle", "12:30", "Date")
        self.assertEqual(self.skill.gui['location'], "Seattle")
        self.assertEqual(self.skill.gui['hours'], "12")
        self.assertEqual(self.skill.gui['minutes'], "30")
        self.assertEqual(self.skill.gui['ampm'], "")
        self.assertEqual(self.skill.gui['date_string'], "Date")
        self.skill.gui.show_page.assert_called_with("time.qml")

        self.skill.gui.show_page = real_gui

    def test_show_date_gui(self):
        real_gui = self.skill.gui.show_page
        self.skill.gui.show_page = Mock()

        date = datetime.datetime.now().replace(year=2023, month=1, day=25)
        self.skill.show_date_gui(date)
        self.assertEqual(self.skill.gui['weekday_string'], date.strftime("%A"))
        self.assertEqual(self.skill.gui['monthday_string'],
                         date.strftime("%B %-d"))
        self.assertEqual(self.skill.gui['year_string'], "2023")
        self.skill.gui.show_page.assert_called_with("date2.qml")
        self.skill.gui.show_page = real_gui

    def test_get_timezone_from_neon_utils(self):
        self.assertEqual(self.skill._get_timezone_from_neon_utils("seattle"),
                         timezone("America/Los_Angeles"))

    @pytest.mark.xfail()  # Nominatim Occasionally Times Out here
    def test_get_timezone_from_builtins(self):
        self.assertEqual(self.skill._get_timezone_from_builtins("seattle"),
                         timezone("America/Los_Angeles"))

    def test_get_timezone_from_table(self):
        self.assertEqual(self.skill._get_timezone_from_table("pacific time"),
                         timezone("America/Los_Angeles"))
        self.assertEqual(self.skill._get_timezone_from_table("eastern time"),
                         timezone("America/New_York"))
        self.assertEqual(self.skill._get_timezone_from_table("china"),
                         timezone("Asia/Hong_Kong"))
        self.assertEqual(self.skill._get_timezone_from_table("paris texas"),
                         timezone("America/Chicago"))

    def test_get_timezone_from_fuzzymatch(self):
        self.assertEqual(self.skill._get_timezone_from_fuzzymatch("los angeles"),
                         timezone("America/Los_Angeles"))


if __name__ == '__main__':
    pytest.main()
