from pynput.keyboard import Key, Listener

def on_press(key):
    print('{0} pressed'.format(
        key))

# Collect events until released
with Listener(
        on_press=on_press) as listener:
    listener.join()