from vnstock_data import Reference

def main():
    print("Hello from stock-filter!")
    print(Reference().equity.list_by_exchange())

if __name__ == "__main__":
    main()
