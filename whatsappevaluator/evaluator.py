from __future__ import annotations

import pandas as pd
from pathlib import Path
from datetime import datetime
import re
import emoji as emoji


# Message layout:
# DD/MM/YYYY, HH:MM - NAME: "Message"
# Multi-line message do not start with DD/MM/YYYY
patterns = {
    "EU": r"^\d{2}/\d{2}/\d{4}, \d{2}:\d{2}",
    "NA": r"^\d{2}/\d{2}/\d{4}, \d{2}:\d{2}",
    "JP": r"^\d{4}/\d{2}/\d{2}, \d{2}:\d{2}",
}
datetimes = {
    "EU": "%d/%m/%Y, %H:%M",
    "NA": "%m/%d/%Y, %H:%M",
    "JP": "%Y/%m/%d, %H:%M",
}


class WhatsappChat:
    def __init__(self, chat_file: Path | str, time_format: str = "EU") -> None:
        """Create WhatsappChat object from a chat backup.

        Parameters
        ----------
        chat_file : Path | str
            File path to the whatsapp chat backup .txt file.
        time_format : str, optional
            Time format used in the messages, Options: ["EU", "NA", "JP"],
            by default "EU"

        """
        if not isinstance(chat_file, Path | str):
            raise ValueError("'chat_file' must be either 'Path' or 'str'.")
        if isinstance(chat_file, str):
            chat_file = Path(chat_file)
        if not chat_file.exists():
            raise ValueError("'chat_file' is not a valid file.")
        if not chat_file.suffix == ".txt":
            raise ValueError("'chat_file' must be a valid .txt file.")
        if time_format not in patterns:
            raise ValueError("'time_format' must be a valid format.")

        # Read the file into a list of lines
        with open(file=chat_file, mode="r", encoding="utf-8") as file:
            lines = file.readlines()

        # Create empty lists to store the data
        times = []
        speakers = []
        messages = []

        # Evaluate the chat line by line, skipping the encryption notice
        for line in lines[1:]:
            match = re.match(patterns[time_format], line)

            # Is the start of a new unique message if no time at start
            if match:
                time = datetime.strptime(
                    re.match(patterns[time_format], line).group(),
                    datetimes[time_format],
                )
                speaker, message = line[20:].split(":", 1)

                times.append(time)
                speakers.append(speaker)
                messages.append(message)

            # New line of existing message
            else:
                messages[-1] = messages[-1] + line

        # Create Pandas DataFrame of all Messages and contents
        chat = pd.DataFrame({"Speaker": speakers, "Message": messages, "Time": times})

        # Create Weekday column
        chat["Weekday"] = chat["Time"].dt.dayofweek
        chat["Weekday"] = chat["Weekday"].replace(
            [0, 1, 2, 3, 4, 5, 6],
            [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
        )

        # Calculate Message length, emoji count and appearance
        chat["Message Length"] = chat["Message"].str.len()
        chat["Emoji Count"] = [emoji.emoji_count(message) for message in chat.Message]
        chat["Contains Emoji"] = chat["Emoji Count"].where(chat["Emoji Count"] == 0, 1)

        # Add as attribute
        self.chat = chat

        # Create aggregate dataframes
        self.daily_chat = self.__aggregate_by_time("D")
        self.weekly_chat = self.__aggregate_by_time("W")
        self.monthly_chat = self.__aggregate_by_time("M")

    def __aggregate_by_time(self, time_aggregator) -> pd.DataFrame:
        aggregated_chat = (
            self.chat.groupby(
                [pd.Grouper(key="Time", freq=time_aggregator), "Weekday", "Speaker"]
            )
            .agg(
                {
                    "Message": ["count"],
                    "Message Length": ["sum"],
                    "Contains Emoji": ["mean"],
                }
            )
            .reset_index()
        )
        aggregated_chat.columns = [
            f"{lvl1}_{lvl2}" if pd.notna(lvl2) and lvl2 != "" else lvl1
            for lvl1, lvl2 in aggregated_chat.columns
        ]
        return aggregated_chat.reset_index(drop=True)

    def __create_():
        pass
