from sqlalchemy.sql import text
from srna_api.extensions import db, ma

class RawSqlProvider:
    def execute_sql_and_fetch_records(self, sql_statement, params):
        results = self.execute_sql(sql_statement, params)
        return self.fetch_dicts(results)

    def execute_sql(self, sql_statement, params):
        results = db.session.execute(text(sql_statement), params)
        db.session.commit()
        return results

    def fetch_dicts(self, results):
        records = []
        for r in results.fetchall():
            records.append(dict(r.items()))
        return records
