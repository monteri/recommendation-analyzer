import faust
import asyncio

TOP_N = 5


class Activity(faust.Record, serializer='json'):
    user_id: str
    activity: str
    param: str


app = faust.App('activity_stream', broker='kafka://localhost:9092')
activity_topic = app.topic('activity_topic', value_type=Activity)

leaderboard_table = app.Table('leaderboard', default=int)


@app.agent(activity_topic)
async def process(activities):
    async for activity in activities:
        print('activity', activity)
        try:
            if activity.activity == "buy":
                leaderboard_table[activity.param] += 1
        except Exception as e:
            # Log or handle the exception
            print(f"Error processing activity: {e}")


async def cleanup_leaderboard():
    while True:
        await asyncio.sleep(300)
        print('Clean up')
        leaderboard_table.clear()


app.task(cleanup_leaderboard)


@app.page('/popular_items/')
async def get_popular_items(self, request):
    # Get items from leaderboard_table
    top_items = sorted([(k, v) for k, v in leaderboard_table.items()], key=lambda x: x[1], reverse=True)[:TOP_N]
    return self.json(top_items)
