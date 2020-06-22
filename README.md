# channelsmin2

This is an minimal example of how I set up django channels 2.2 in oTree apps for oTree > 2.5.8, as described <a href="https://otree.readthedocs.io/en/latest/misc/django.html#real-time-and-websockets"> in the oTree documentation</a>.

Older versions of this project demonstrated how to use channels 1.x for oTree < 2.3.0b5.  You can check out versions from March 19 2019 or before for that revision.  For versions between 2.3.0b5 and 2.5.8, see the revisions before June 22 2020.


It loads a page which has a single button which forwards every member of the group to the next page when any single player clicks it.<br>
You can see a demo here: https://channelsmin.herokuapp.com/demo/

To set up your existing oTree installation to use this scheme, you need to add a line to the end of your settings.py (if you don't have an EXTENSION_APPS defined already):<br>
<code>EXTENSION_APPS = []</code>


For each app which uses channels, you need to:<br>
<ol>
<li>
  Add one entry into your settings.py's EXTENSION_APPS list with the name of your app.  In our case, our EXTENSION_APPS will now be:
  <br><code>EXTENSION_APPS = ['channelsmin']</code>
</li>
<li>
  Add a consumers.py to the root directory of your new app which defines the consumer you intend to use.  There are 5 functions to implement based on oTree's _OTreeJsonWebsocketConsumer class.  It's also possible to write a simpler consumer like in the <a href="https://channels.readthedocs.io/en/latest/tutorial/part_2.html#enable-a-channel-layer">Channels tutorial</a> but I've chosen to use oTree's model.   
</li>
<li>
  Add an otree_extensions/routing.py to your app like the one defined in this example, being careful to create a custom websocket URL for your app, and referring to the consumer defined above.
</li>

<li>Add javascript functionality to your page which sets up the websocket (using the URL pattern defined in your routing.py) and connects and also other functionality to actually do what you need to do in your app.  See this example's MyPage.html for reference.</li>
</ol>
A tricky bit of this setup is that the URLS in your channel routing need to match the URLS you specify as paths in your html templates.  So if you're not getting connections, troubleshoot those.
