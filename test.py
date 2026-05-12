from intasend import APIService

API_PUBLISHABLE_KEY='ISPubKey_test_4f02220a-b88b-48f8-be7e-b5b97957be5c'

API_TOKEN = 'ISSecretKey_test_73e878cb-b90b-4c81-b4df-af746ca8d459'

service = APIService(token=API_TOKEN,publishable_key=API_PUBLISHABLE_KEY,test=True)

create_order = service.collect.mpesa_stk_push(phone_number='254712345678', email= 'test@gmail.com',amount=100,
                                            narrative='Purchase of items')

print(create_order)

