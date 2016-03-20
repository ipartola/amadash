# amadash

Amazon Dash button monitor inspired by [edwardbenson](https://medium.com/@edwardbenson/how-i-hacked-amazon-s-5-wifi-button-to-track-baby-data-794214b0bdd8#.77z7gdnvg)
and [jgrahamc](https://github.com/jgrahamc/dash). Unlike other solutions, amadash is a self-contained package which does not
require the user to modify any code to react to button presses. It includes all the functionality necessary to run as a
daemon and is entirely driven by a simple config file.

## Installation

For Debian/Ubuntu/Raspbian:

    sudo apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 2272781B
    echo "deb http://debs.ridgebit.net/amadash/ custom main" | sudo tee /etc/apt/sources.list.d/amadash.list
    sudo apt-get update
    sudo apt-get install amadash

For all others:

    git clone --recursive git@github.com:ipartola/amadash.git
    cd amadash
    virtualenv .env
    . .env/bin/activate
    pip install -r requirements.txt
    python setup.py install
    mkdir tmp
    cp conf/example.conf tmp/amadash.conf

To run amadash in this setup:
    amadash -c tmp/amadash.conf

## Button setup

To set up your Amazon Dash button you will need to use an Android or iOS device with the Amazon app installed. The steps are as follows:

1. Connect the button to your Wi-Fi. Ensure that the button is connected to the same network as the machine on which you
   intend to run amadash.
2. Do not select a product to order in the final step. You may want to turn off push notifications to the Amazon app,
   otherwise it will annoy you every time you press the button.
3. Grab the MAC address from the button; see next section.

## amadash configuration

In order to configure your Amazon Dash buttons you will need to detect their MAC addresses. You can use WireShark or tcpdump
as described in the original blog post by edwardbenson. An easier way to do this is to run the amadash-discover tool:

    sudo amadash-discover

Once `amadash-discover` is running, press the button which you are trying to discover. The MAC address will be printed
out.

NOTE: if you get an error like `Could not initialize packet capture interface: not a broadcast link`, try explicitly
specifying the network interface:

    sudo amadash-discover -i eth1

Next, edit your /etc/amadash.conf and add the button's name, MAC address, and action you'd like it to perform. For example:

    [button:0]
    name = Button 0
    mac = f0:27:00:00:00:01
    action = /usr/bin/curl -s "https://example.com/?button=$BUTTON_NAME&mac=$BUTTON_MAC"
    
    [button:1]
    name = Button 1
    mac = f0:27:00:00:00:02
    action = echo "Button $BUTTON_NAME was pressed!" | mail -s 'New button press' me@example.com

After you are done editing the config file, restart amadash. On Debian/Ubuntu/Raspbian:

    sudo /etc/init.d/amadash restart

## Contributing

To contribute to this project, simply fork it, modify the code, then create a pull request.

To set up local development:

    git clone --recursive git@github.com:ipartola/amadash.git
    cd amadash
    virtualenv .env
    . .env/bin/activate
    pip install -r requirements.txt
    python setup.py develop
    mkdir tmp
    cp conf/example.conf tmp/amadash.conf
    amadash -c tmp/amadash.conf

Currently looking for someone to help out with:
 * Creating an RPM package.
 * Creating a homebrew package
 * Creating a FreeBSD port

