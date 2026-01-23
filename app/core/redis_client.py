import redis

redis_client = redis.Redis(
    host="10.140.242.176",
    port=6379,
    db=0,
    decode_responses=True,
    socket_connect_timeout=5,  # fail fast if unreachable
    socket_timeout=5,
)

# Optional: verify connection on startup
try:
    redis_client.ping()
    print("✅ Connected to Redis at 10.140.242.176:6379")
except redis.ConnectionError as e:
    print("❌ Redis connection failed:", e)
