import requests


user_infos={
    "Authorization":"Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNDZhOGYwMi1kMTkwLTQzM2YtODc5Yi01ZDdkMTYxMDEyZGMiLCJ1c2VyX2lkIjoiMTQ2YThmMDItZDE5MC00MzNmLTg3OWItNWQ3ZDE2MTAxMmRjIiwic2VydmljZV9uYW1lIjoiSFlQRVJMT0NBTC1JTlZFTlRPUlkiLCJ0eXBlIjoiYWNjZXNzIiwidmVyc2lvbiI6IjEiLCJleHAiOjE3ODczMTA5ODUsImp0aSI6IjRmZDVjN2FjLTMyZGYtNDA5OS1iOGFhLTcxYzk5ZGI5YmEyOSIsImVtYWlsIjoidGVzdGluZzEyY3Rlc3RpbmdAZ21haWwuY29tIiwibW9iaWxlbnVtYmVyIjoiKzkxODI0ODY5MjgzOSJ9.FWt3Ht0YAYdIzSn8tunVquk5LYB70Vb0gl2946GdtjuB_a-sIGAHcjCFQinnzcCoihYX4qE8LVj87DLYXmlxpAm_6x1TG5h6cAS0Ntzr81iV1jXoTkWEY5lAKgmkwuHyeGxOpDIuqVV__BnbinA8pzI_-WyNdW8f5IaLTDxA2SZ2OfJPcjHLxz0hNxSMfGmZq_uMG9I_sstj0fI7_1uTl8bX6rv3_lKSuSA-rietm34VyWxRoq_ZwZRSSZDzcuDjfMqK-tTtagOTiVvkGpAkWW5kPcmtzuYtJ9Ws-FeoNqInvvThwRf_l4FyqK1IdWKn321n_LtHHLmHs01zibas4A",
    "X-User-Infos":'{"user_id":"146a8f02-d190-433f-879b-5d7d161012dc","role":"customer"}',
    "X-Shop-Id":"e74ade9c-7f46-5d7f-b8bf-60e99ff34687"
}


res=requests.get(
    "http://127.0.0.1:8900/api/employees/modules/allowed",
    headers=user_infos
)

print(res.text)

print(res.json())