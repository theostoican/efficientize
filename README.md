# efficientize
> Do you often find yourself at the end of the day wondering how the time passed by so fast ? Many people struggle with this kind of feeling and they desperately try to remember how much time they really spent working and how much time recreating. I am one such example. If you are the same and want to gain some insight in your everyday activity at the computer (especially if you are a computer progammer), you've arrived at the right place.

## What is it?
**efficientize** is an app that helps you visualize your daily activity in a more accurate way without any personal biases that people usually have when they start analyzing their performance. But, no more words, and let us see how it works.
## How does it work ?
The app is accessible in the browser and provides a Home page, from which you can access the relevant information for multiple dates.
![alt text](https://github.com/theostoican/efficientize/blob/master/images/home.png)
If you click on the blue text, you will open a timeline-like visualization tool, that helps you visualize, for each hour recorded during the day how much time you spent having a particular app open and how many keystrokes you have pressed. The timeline information preserves the original order in which you have worked during the day and displays it in small bars along the x axis. On the y axis, you have 4 **categories** that show you how much you typed while having that app open. Hovering over the timeline displays more intimate information (the *name* of the app, the exact *interval* and the *frequency of keystrokes*).
![alt text](https://github.com/theostoican/efficientize/blob/master/images/timeline.png)
From the top-left side of the timeline interface (and from the home page as well), you can access another type of visualization. Clicking the *Show stats* button leads you to the following, more statistically relevant page:
![alt text](https://github.com/theostoican/efficientize/blob/master/images/time.png)
Here you can visualize some statistics regarding the apps in which you spent the largest amount of time. In the pie chart, on the one hand, you can see how the time you spent on the top 5 apps fits into the larger picture and how the time you spent on each activity relates to the total time. On the bar chart, on the other hand, you can see a top 10 of the apps in which you spent most of the time. In the example from above, you can see that on 25th September, I spent most of day in a *Chrome* Page, entitled **Time's Up Marinara** (approximately *14 hours and 22 minutes*). That is because I left the app open over night and when I finished the work and took a pause, and the *Marinara* timer opened a page in browser, telling me that I should start working.

A similar statistics is available for keystrokes as well (by clicking on the second *Tab* - **Keystrokes statistics**). Similarly to the previous *Tab*, you can examine the data in both the pie chart (for *overview*) and the bar chart (for *a top*), while hovering provides more intimae details (including the *frequency* of keystrokes). For example, on the same day as above, the app recorded roughly 2000 keystrokes while editing this README :).
![alt text](https://github.com/theostoican/efficientize/blob/master/images/keystrokes.png)
> How is it made?
**efficientize** is made in pure *Python* and it uses for visualization a nice framework named *Dash*, which is based on *Plotly*. If you want to read more about Dash, take a look [here](https://dash.plot.ly/).

The main reason why I have chosen Dash is because, after careful analysis, I came to the conclusion that it was the *best* framework (if not the *only*) that fulfils the following requiremens:
* Robustness
* Strong community
* Solid Documentation
* Intuitive API
* Provides multi-page support
* Renders the app as Single Page App
* Intuitive and nice-looking charts
## Usage
In the root of the project directory run:
* *pip install -r requirements.txt*
* *python index.py*
## Follow-up
The things that still need to be done consist of ithe following:
* Currently the app supports visualizing the newest updates in the current day only by refreshing. The ultimate goal would be to make the app update itself in real time.
* Incorporate a Pomodoro timer and outline in the timeline (and maybe in statistics as well) the time spent on an open app during a Pomodoro and a pause.
## License
MIT
