# channelsmin

This is an minimal example of how I set up django channels 1.0 in oTree apps.  It loads a page which has a single button which forwards every member of the group to the next page when any single player clicks it.

To set up your existing oTree installation to use this scheme, you'll have to copy over routing.py and add one line to the end of your settings.py:<br>
<code>CHANNEL_ROUTING = 'routing.channel_routing'</code>


For each app which uses channels, you need to:<br>
<ol>
<li>
  Add one import line (importing your app's three channels functions as unique names) and three 'route' lines (one for each channels function) to the routing.py
</li>
<li>
  Add a consumers.py to your new app which defines these three functions  
</li>
<li>Add javascript functionality to your page which sets up the websocket and connects and also other funcitonality to actually do what you need to do in your app</li>

The trickiest bit of this setup is that the URLS in your channel routing need to match the URLS you specify as paths in your html templates.  So if you're not getting connections, troubleshoot those.
