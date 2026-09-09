from django.conf import settings
from datetime import datetime
import requests
import base64
from ..models import Booking

STK_PUSH_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

def get_metadata_value(items, name):
    for item in items:
        if item["Name"] == name:
            return item.get("Value")

    return None

def generate_timestamp():
    return datetime.now().strftime("%Y%m%d%H%M%S")

def generate_password(timestamp):
   password_string = (
      settings.MPESA_SHORTCODE +
      settings.MPESA_PASSKEY +
      timestamp
   )

   #converting to bytes
   password_bytes = password_string.encode("utf-8")

   #base64 encoding
   encoded_password = base64.b64encode(password_bytes)

   #converting encoded password to string for use in the JSON request
   return encoded_password.decode("utf-8")

def get_access_token():
  url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

  consumer_key = settings.MPESA_CONSUMER_KEY
  consumer_secret = settings.MPESA_CONSUMER_SECRET

  #send the request
  try:
      response = requests.get(
        url,
        auth = (consumer_key, consumer_secret)
      )


      #verify the request succeeded
      response.raise_for_status()

      #read the JSON response
      data = response.json()

      return data['access_token']

  except requests.exceptions.RequestException as e:
     print(f"Error getting access token: {e}")
     return None

def stk_push(phone_number, amount, account_reference, transaction_desc):
   access_token = get_access_token()

   if access_token is None:
    raise Exception("Failed to obtain M-Pesa access token")

   timestamp = generate_timestamp()

   password = generate_password(timestamp)

   headers = {
      "Authorization" : f"Bearer {access_token}",
      "Content-Type" : "application/json"
   }

   payload = {
      "BusinessShortCode" : settings.MPESA_SHORTCODE,
      "Password" : password,
      "Timestamp" : timestamp,
      "TransactionType" : "CustomerPayBillOnline",
      "Amount" : amount,
      "PartyA" : phone_number,
      "PartyB" : settings.MPESA_SHORTCODE,
      "PhoneNumber" : phone_number,
      "CallBackURL" : settings.MPESA_CALLBACK_URL,
      "AccountReference" : account_reference,
      "TransactionDesc" : transaction_desc,

   }

   try:
      response = requests.post(
          STK_PUSH_URL,
          headers=headers,
          json=payload,
          timeout=30
          
      )

      response.raise_for_status()

      return response.json()

   except requests.exceptions.RequestException as e:
      raise Exception (f"STK Push Request failed: {e}") from e        

def process_callback(callback):

    checkout_request_id = callback["CheckoutRequestID"]
    merchant_request_id = callback["MerchantRequestID"]
    result_code = callback["ResultCode"]
    result_desc = callback["ResultDesc"]

    booking = Booking.objects.get(
        checkout_request_id=checkout_request_id
    )

    booking.merchant_request_id = merchant_request_id

    if result_code != 0:

        booking.payment_status = "FAILED"
        booking.save()

        return

    metadata = callback["CallbackMetadata"]["Item"]

    amount = get_metadata_value(metadata, "Amount")
    receipt_number = get_metadata_value(
        metadata,
        "MpesaReceiptNumber"
    )

    transaction_date = get_metadata_value(
        metadata,
        "TransactionDate"
    )

    phone_number = get_metadata_value(
        metadata,
        "PhoneNumber"
    )

    booking.payment_status = "SUCCESS"
    booking.mpesa_receipt_number = receipt_number
    booking.payment_phone = phone_number
    booking.payment_transaction_date = transaction_date

    booking.save() 