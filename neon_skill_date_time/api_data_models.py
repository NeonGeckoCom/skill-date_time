# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2025 Neongecko.com Inc.
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

from typing import Optional
from pydantic import BaseModel, RootModel, Field


class TimeInLocationRequest(BaseModel):
    location: Optional[str] = Field(
            default=None, description="Location to get time information for")


class DisplayDateReponse(RootModel):
    root: str = Field(description="Date in the user-configured format")


class DisplayCurrentTimeResponse(RootModel):
    root: str = Field(description="Current time in the user-configured format")


class WeekdayResponse(RootModel):
    root: str = Field(description="Weekday printed in the user's language")


class MonthDateResponse(RootModel):
    root: str = Field(description="Month and day in the user-configured format")


class YearResponse(RootModel):
    root: str = Field(description="Year (YYYY)")


class CurrentTimeResponse(RootModel):
    root: float = Field(description="Current epoch time in seconds")


class FormattedTimeResponse(BaseModel):
    formatted_time: str = Field(description="Current time in HH:MM format")
    formatted_date: str = Field(description="Current date in YYYY-MM-DD format")
    current_weekday: str = Field(description="Current weekday name in English")
