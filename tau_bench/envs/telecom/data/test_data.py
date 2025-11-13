import json 

with open("customers.json", "r") as f:
    CUSTOMER_DATA = json.load(f)

with open("devices.json", "r") as f:
    DEVICES_DATA = json.load(f)

with open("services.json", "r") as f:
    SERVICES_DATA = json.load(f)

with open("billing.json", "r") as f:
    BILLING_DATA = json.load(f)


def test_customer_data(): 

    for customer_id, customer in CUSTOMER_DATA.items():
        for device in customer["devices"]:

            try: 
                assert device["name"] in DEVICES_DATA
            except AssertionError:
                print(f"Device {device['name']} not found in devices data")
                raise AssertionError(f"Device {device['name']} not found in devices data")
            try: 
                assert device["service"] in SERVICES_DATA
            except AssertionError:
                print(f"Service {device['service']} not found in services data")
                raise AssertionError(f"Service {device['service']} not found in services data")

    for customer_id, customer in CUSTOMER_DATA.items():
        for service in customer["services"]:
            assert service in SERVICES_DATA
    
    print("Customer data is valid")

def test_billing_data():
    #load the billing data
    for customer_id, billing in BILLING_DATA.items():
        assert customer_id in CUSTOMER_DATA
        for service, charge in billing["monthly_charges"].items():
            try: 
                assert service in SERVICES_DATA
            except AssertionError:
                print(f"Service {service} not found in services data")
                raise AssertionError(f"Service {service} not found in services data")
            try: 
                assert charge == SERVICES_DATA[service]["price"]
            except AssertionError:
                print(f"Charge {charge} for service {service} does not match price in services data")
                raise AssertionError(f"Charge {charge} for service {service} does not match price in services data")
            
            try: 
                assert service in CUSTOMER_DATA[customer_id]["services"]
            except AssertionError:
                print(f"Service {service} not found in customer {customer_id} services")
                raise AssertionError(f"Service {service} not found in customer {customer_id} services")
            
    
    print("Billing data is valid")

if __name__ == "__main__":
    test_customer_data()
    test_billing_data()