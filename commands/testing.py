from typing import Optional

from objects.Exceptions import MySQLException

sqlUpdateReminder = """
INSERT INTO fap_predictions ( id, `user`, user_id, recruit_name, recruit_profile, recruit_class, team, confidence, prediction_date, correct, decision_date, committed_team ) VALUES ( % s, % s, % s, % s, % s, % s, % s, % s, % s, NULL, NULL, NULL ) ON DUPLICATE KEY UPDATE ( team = % s, confidence = % s, prediction_date = % s )
"""


class SqlQuery:
    def __init__(
        self,
        query: str,
        values: Optional[tuple[str, ...]] = None,
        fetch: Optional[str] = None,
    ) -> None:
        s_count = query.count("% s")
        if len(values) != query.count("% s"):
            raise MySQLException(
                f"Not enough values provided. {len(values)} provided bu {s_count} expected."
            )
        self.query: str = query
        self.values: Optional[tuple[str]] = values
        self.fetch: Optional[str] = fetch
        self.processed_query = self.query.replace(
            "\n", ""
        )  # SQL must be "SQL Minify" from https://codebeautify.org/sqlformatter

        for value in self.values:
            self.processed_query = self.processed_query.replace("% s", str(value), 1)

    def __str__(self) -> str:
        return self.processed_query

    def __repr__(self) -> str:
        return self.processed_query


if __name__ == "__main__":
    v = SqlQuery(
        sqlUpdateReminder,
        (
            "aaaaaa1",
            "12312312b",
            "c3232",
            "d321312",
            "asdfafs",
            "dsfafasfsa",
            "sfasfsa",
            "ewrewrew",
            "ccvsfe",
            "dsffsfsd",
            "sdfasfasf",
            "sdfsfsadf",
        ),
    )
    print(v)
