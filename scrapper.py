import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA

# Function to get the price from Amazon
def get_amazon_price(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
        'Accept-Language': 'en-US, en;q=0.5'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "lxml")

    try:
        price_element = soup.select_one('span.a-price.aok-align-center.reinventPricePriceToPayMargin.priceToPay')
        if price_element:
            price_whole = price_element.find('span', {'class': 'a-price-whole'}).text.strip().replace(',', '')
            price_fraction = price_element.find('span', {'class': 'a-price-fraction'}).text.strip() if price_element.find('span', {'class': 'a-price-fraction'}) else '00'
            price = f"{price_whole}.{price_fraction}"
            return float(price)
        else:
            raise ValueError("Price element not found on the page.")
    except AttributeError as e:
        print(f"Error parsing price: {e}")
        return None

# Function to scrape Amazon product details
def main(URL):
    File = open("out.csv", "a")

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
        'Accept-Language': 'en-US, en;q=0.5'
    }

    webpage = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(webpage.content, "lxml")

    try:
        title = soup.find("span", attrs={"id": 'productTitle'})
        title_value = title.string
        title_string = title_value.strip().replace(',', '')
    except AttributeError:
        title_string = "NA"
    print("Product Title = ", title_string)
    File.write(f"{title_string},")

    price = get_amazon_price(URL)
    if price:
        print(f"Product Price = ₹{price}")
        File.write(f"{price},")
    else:
        price = "NA"
        File.write(f"{price},")
        print("Price not found.")

    try:
        rating = soup.find("i", attrs={'class': 'a-icon a-icon-star a-star-4-5'}).string.strip().replace(',', '')
    except AttributeError:
        try:
            rating = soup.find("span", attrs={'class': 'a-icon-alt'}).string.strip().replace(',', '')
        except:
            rating = "NA"
    print("Overall Rating = ", rating)
    File.write(f"{rating},")

    try:
        review_count = soup.find("span", attrs={'id': 'acrCustomerReviewText'}).string.strip().replace(',', '')
    except AttributeError:
        review_count = "NA"
    print("Total Reviews = ", review_count)
    File.write(f"{review_count},")

    try:
        available = soup.find("div", attrs={'id': 'availability'}).find("span").string.strip().replace(',', '')
    except AttributeError:
        available = "NA"
    print("Availability = ", available)
    File.write(f"{available},\n")
    File.close()

# Function to predict prices using ARIMA
def predict_price(data_file='historical_prices.csv'):
    try:
        historical_data = pd.read_csv(data_file)
    except FileNotFoundError:
        historical_data = pd.DataFrame(columns=['ds', 'y'])

    url = 'https://amzn.in/d/0grEEEMs'
    price = get_amazon_price(url)

    if price is not None:
        current_data = pd.DataFrame({
            'ds': [datetime.now()],
            'y': [price]
        })
        data = pd.concat([historical_data, current_data])
        data.to_csv(data_file, index=False)

        model = ARIMA(data['y'], order=(5, 1, 0))
        model_fit = model.fit(disp=0)
        forecast = model_fit.forecast(steps=30)[0]

        plt.plot(data['ds'], data['y'], label='Actual Prices')
        plt.plot([data['ds'].iloc[-1] + pd.Timedelta(days=i) for i in range(1, 31)], forecast, label='Forecasted Prices')
        plt.title('Amazon Price Prediction')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.show()

        forecast_df = pd.DataFrame({
            'ds': [data['ds'].iloc[-1] + pd.Timedelta(days=i) for i in range(1, 31)],
            'yhat': forecast
        })
        forecast_df.to_csv('price_forecast.csv', index=False)
        print(forecast_df.tail())

if __name__ == '__main__':
    url = 'https://www.amazon.in/boAt-Nirvana-Technology-Detection-Bluetooth/dp/B0BW8TXJJ2/ref=sr_1_2?_encoding=UTF8&content-id=amzn1.sym.48d2178a-5f7b-4af5-98b8-fc7b096852d4&dib=eyJ2IjoiMSJ9.70ic9OuEM7Cm26Ed-JeghFj2Vecy_W5TUbyw3SLLn-DFME6Ep6EO2c7zCK8K66GUukb4qh3URv8S7OjqOPsnw7ZUrMb5i-zBkC-Qo-G374wkpJduqNdhjJX-kbGpsOq0z4BwiOioI3K_rbWffNGxy59SVNK_GvkXxKbc_mzRLStITbNYVgg-66PKNQ2gwkaqlwQ1qRbUFvMdf0ENHnxeIX2XMdsqgOot5ZohEEl7-U0NhbvWXlcGlg-npwvozD7NO-nxB9or705NnuxIa7qJuBhY2dkbxZXT1__VMDudvDA.NIylEPRGRACDFqIMYBv73JpqnbO8h3aEULpESlgkilA&dib_tag=se&pd_rd_r=9c13dccc-6e30-4ce8-aeb0-585c310569d3&pd_rd_w=DKzpt&pd_rd_wg=DDzgP&pf_rd_p=48d2178a-5f7b-4af5-98b8-fc7b096852d4&pf_rd_r=CM5NDZKG5B42YBNWEKCB&qid=1722158038&refinements=p_89%3AboAt&s=electronics&sr=1-2'
    main(url)
    predict_price()
