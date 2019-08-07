# Curriculum

## Question
- how do we assess prior knowledge and understanding?
-

# (1) Why do my devices communicate with different companies?
## Welcome!
By now you probably have plugged in a number of different devices, and you have observed how the Aretha interface shows data flows from connected devices.

You then probably clicked some of the company names to learn more about them, and you looked at the map to see where the companies are located
![company-names](figures/aretha-annotated.png)

Looking at the map, you have probably also realised that every device you connected is sending data to more than on location (company), and maybe you've been wondering why that is the case, and how the receiving company might use the data.


Over the next few weeks, you will learn a little more about _**how these devices work**_, _**how data is collected and transferred**_, and _**how that data might be used**_.



## How are my devices connected to the internet?

![smart home device landscape](figures/landscape-01.svg)

1) activity tracker example: records information, transfers this to fitbit using a mobile app
2) smart tv: streaming video from netflix requires TV to be connected to the internet
3) smart outlet: use mobile app to switch on/off smart outlet via the internet from home or away

## Why do my devices communicate with different companies?
On a smart TV, you would be logged into different 'apps', and these apps communicate with their provides: Amazon Prime Videos, Netflix, Now TV, BBC iPlayer and so on. Say it's a Samsung Smart TV. It might also share information with Samsung, such as your software version or any error reports. If you see some ads, then these ads might be loaded from another company all together.

The information smart device use and the information they collect are of particular importance to their manufacturers. There’s a lot of discussion about data collection, but little about why companies might want to collect data. Here are four of the main reasons, covering a broad range of applications.

1) **Service provision** - the most obvious reason for collecting data is that it’s needed in order to provide you with a service or to make recommendations to you (e.g. a company can’t charge you for something without your bank details, or suggest films without knowing what you like to watch)
2) **Advertising** - companies often include advertising code from other companies on their websites and apps in order to make ad revenue. This extra code often collects information about you and combines this with information from other sources in order to show you ads for products you’re more likely to click on and buy
3) **Product analytics** - companies often want to know which parts of their platforms are used the most. This is useful when improving the service they offer, as well as to help them market it more effectively to new customers
4) **Behavioural insights** - used to learn more about why users take particular actions, either to develop the product, improve marketing efforts, or tailor advertisements (e.g. analysing Alexa recording to create better speech recognition models)

#### Question
Please answer the following for any device connected to Aretha.

1) State which device you are talking about (with its name from the interface).
2) List the companies it communicates with and explain why it might be communicating with the respective company. Use any of the main reasons or add your own.

# (2) How do they connect through the internet?

## Recap
In the previous lesson, you've learned why your devices communicate with different companies. You've been introduced to four main reasons for companies to collected data: (1) service provisioning, (2) advertising, (3) product analytics, and (4) behavioural insights. We also asked you to explain why one of your devices sends data to different companies.

So far, we've looked at the internet as a black cloud (picture below). We know that transferring data from devices to companies uses the internet but we haven't looked at how that is actually accomplished. This lessons takes a closer look at what the internet acutally is and how it works.
![](figures/landscape-02.svg)

## How do my devices connect to companies over the internet?
The internet is a global network of computers, some of which are called web servers. A web server is a computer which hosts websites for other computers to access over the internet. A web server may host a single website or many websites. Similarly, web servers also provide web services with which smart devices can communicate.

But how do you connect to a website? When you make a telephone call, a connection is formed between you and the person you are calling that goes through different telephone exchanges. Similarly, a connection between you and a web server will go through many different computers. A web server also needs to be able to connect to many different computers at the same time (like being on the phone with five people at once). Information sent between the web server and other computers is broken up into smaller chunks called data packets. Not only is it more efficient to route these smaller packets between computers, but it also saves time if one is lost and needs to be sent again.

<p><iframe height="315" src="https://www.youtube.com/embed/5o8CwafCxnU?start=0&amp;end=164&amp;controls=0" width="560"></iframe></p>

# (3) Why do some companies have locks next to their names?

## Recap

tbd


context and relevance to smart devices



## Why do some companies have locks next to their names?
Originally, information on the internet was sent in clear text. Informaion sent like this can be tampered with or spoofed by attackers (hackers). Many modern devices and services combat this by protecting your information using encryption.

### Encyrption
Secure protocols like Secure Socket Layer (SSL) or Transport Layer Security (TLS) protect your information by making it unreadable to hackers, like a secure layer wrapped around your data. This is what is happening when you see the padlock icon in your browser when acessing https:// sites.

### Authentication
The same protocols also verify the server certificate, making sure that the device is communicating with the correct server. With out this authentication, data might still be encrypted but you might unknowingly communicate with an imposter.


<p><iframe height="315" src="https://www.youtube.com/embed/kBXQZMmiA4s?start=281&amp;end=365&amp;controls=0" width="560"></iframe></p>



## Example
Not all of the data your devices are sending or receiving is encrypted. Encryption requires a lot of computation, which can be difficult for small devices, and adds complexity to communications. This is fine when the information being sent isn't sensitive, but can cause major problems otherwise.

For example, imagine a smart bathroom scale that sends data (hypothetically) to two different companies:
1) The manufacturer to store weight measurements
2) AccuWeather to request tomorrow's forecast

### Encryption
The weather forecast is fine to send unencrypted - there's little danger if anyone else is able to read them - but weight measurements from the bathroom scale reveal sensitive information about your current well-being and fitness level, as well as the time of the day at which you tend to use the scale. This information could be interesting for insurance companies or even burglars.

### Authentication
The weather forecast is probably equally fine to be send without authentication. Worst case, a wrong forecast would be displayed on the bathroom scale.
Sending your weight measurements to another server than the intended one, would be as dangerous as sending it unencrypted in the first place.


## Question
Please answer the following for any device connected to Aretha.

1) State which device you are talking about (with its name from the interface).
2) List the companies it communicates with, if the communication is encrypted, and explain why it might be communicating with the respective company. Use any of the main reasons or add your own.
3) For each company, what to do you think is their reason to use encryption?
