def clean_sql(query: str) -> str:
    query = query.strip()

    if query.startswith("```"):
        query = query.replace("```sql", "").replace("```", "").strip()

    return query
