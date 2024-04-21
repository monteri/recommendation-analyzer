import json
from confluent_kafka import Consumer, KafkaError, KafkaException
from django.core.management.base import BaseCommand
from src.utils.mongo import insert_event  # Ensure this utility function is properly defined


class Command(BaseCommand):
    help = 'Run Kafka Consumer'

    def handle(self, *args, **kwargs):
        consumer_conf = {
            'bootstrap.servers': 'localhost:9092',
            'group.id': 'django_group',
            'auto.offset.reset': 'earliest',
        }

        consumer = Consumer(consumer_conf)

        try:
            consumer.subscribe(['activity_topic'])

            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        self.stdout.write(f'End of partition reached {msg.topic()}/{msg.partition()}')
                    else:
                        raise KafkaException(msg.error())
                else:
                    # Successful message
                    self.handle_message(msg)
        finally:
            # Close down consumer to commit final offsets.
            consumer.close()

    def handle_message(self, msg):
        """
        Handle the Kafka message.
        """
        try:
            value = msg.value().decode('utf-8')
            event_data = json.loads(value)  # Assuming the message is in JSON format
            insert_event(event_data)  # Insert the event data into MongoDB
            self.stdout.write(f"Inserted Message: {value}")
        except json.JSONDecodeError as e:
            self.stderr.write(f"Error decoding message: {msg.value()}")
        except Exception as e:
            self.stderr.write(f"Error inserting into MongoDB: {e}")
