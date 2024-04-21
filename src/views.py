import json
import requests

from confluent_kafka import Producer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from sklearn.metrics.pairwise import cosine_similarity

from src.data import data
from src.utils.ml_utils import get_recommendations, load_model, load_mapping
from src.utils.mongo import get_event_data

conf = {
    'bootstrap.servers': 'localhost:9092'
}
producer = Producer(conf)
model = load_model()
dataset = load_mapping('dataset.pkl')
item_features = load_mapping('item_features.pkl')
tfidf_vectorizer = load_mapping('tfidf_vectorizer.pkl')
item_features_matrix = load_mapping('item_features_matrix.pkl')


def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result. """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))


@csrf_exempt
def log_activity(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        activity = request.POST.get('activity')
        param = request.POST.get('param')

        message = json.dumps({'user_id': user_id, 'activity': activity, 'param': param})

        producer.produce('activity_topic', value=message, callback=delivery_report)

        # Ensure any outstanding events are cleared and delivery callbacks are invoked before we exit.
        producer.flush()

        print(message)
        return JsonResponse({'message': 'Activity logged successfully'})

    return JsonResponse({})


@csrf_exempt
def get_data(request):
    return JsonResponse(data, safe=False)


@csrf_exempt
def popular_items(request):
    try:
        # Make a GET request to the Faust endpoint
        response = requests.get("http://127.0.0.1:6066/popular_items/")
        response.raise_for_status()

        # Convert the response to JSON
        popular_data = response.json()

        # Return the data as a JsonResponse
        return JsonResponse(popular_data, safe=False)

    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def get_user_recommendations(request):
    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Provide user_id'}, status=400)

    top_n_recommendations = get_recommendations(model, dataset, user_id, data, item_features)

    print(f"Top {5} recommendations for user {user_id}: {top_n_recommendations}")
    return JsonResponse({'result': top_n_recommendations})


@csrf_exempt
def get_content_based_recommendations(request):
    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Provide user_id'}, status=400)

    # Assume 'user_interactions' is a list of product IDs that the user has interacted with
    # You need to implement the logic to retrieve this data
    user_interactions = get_event_data()

    # Create the user profile by averaging the item feature vectors that the user has interacted with
    user_profile = tfidf_vectorizer.transform(user_interactions).mean(axis=0)

    # Calculate the cosine similarity between the user profile and all item features
    cosine_similarities = cosine_similarity(user_profile, item_features_matrix)

    # Get the top N item indices with the highest similarity scores
    top_n_indices = cosine_similarities.argsort()[0][-5:][::-1]

    # Get the recommended item IDs based on the indices
    # Assuming you have a way to map indices back to item IDs
    recommendations = list(filter(lambda x: x['id'] in top_n_indices, data))

    print(f"Top {5} recommendations for user {user_id}: {recommendations}")
    return JsonResponse({'result': recommendations})
