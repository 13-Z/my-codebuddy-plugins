from memory_service import get_memory_service
s = get_memory_service()
for d in [7, 15, 30]:
    c = s.list_cleanup_candidates(older_than_days=d, importance_max='medium', limit=20)
    print(f'days={d}, candidates={len(c)}')
