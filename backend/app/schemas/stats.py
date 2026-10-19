from pydantic import BaseModel


class SourceCount(BaseModel):
    openai: int
    heuristic: int
    fallback: int


class PeriodStats(BaseModel):
    total: int
    by_source: SourceCount


class StatsResponse(BaseModel):
    last_24h: PeriodStats
    all_time: PeriodStats