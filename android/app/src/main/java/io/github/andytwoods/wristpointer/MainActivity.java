package io.github.andytwoods.wristpointer;

import android.app.Activity;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.WindowManager;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.garmin.android.connectiq.ConnectIQ;
import com.garmin.android.connectiq.IQApp;
import com.garmin.android.connectiq.IQDevice;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Relays messages from the Wrist Pointer watch app to the Mac as UDP datagrams.
 * Keep this screen open while presenting. Leave "Mac IP" blank to broadcast on the Wi-Fi.
 */
public class MainActivity extends Activity {
    static final String WATCH_APP_ID = "d4a05089620d44b2b358fa6e58229ed6";
    static final int PORT = 47800;

    private ConnectIQ connectIQ;
    private final IQApp watchApp = new IQApp(WATCH_APP_ID);
    private final ExecutorService net = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());
    private DatagramSocket socket;
    private volatile String macIp = "";
    private volatile int relayed = 0;
    private volatile String lastMessage = "";
    private volatile String state = "Starting Connect IQ...";
    private TextView status;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        SharedPreferences prefs = getPreferences(MODE_PRIVATE);
        macIp = prefs.getString("macIp", "");

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(48, 96, 48, 48);
        TextView label = new TextView(this);
        label.setText("Mac IP (blank = broadcast)");
        EditText ipField = new EditText(this);
        ipField.setText(macIp);
        ipField.setSingleLine();
        ipField.addTextChangedListener(new TextWatcher() {
            public void beforeTextChanged(CharSequence s, int a, int b, int c) {}
            public void onTextChanged(CharSequence s, int a, int b, int c) {}
            public void afterTextChanged(Editable s) {
                macIp = s.toString().trim();
                prefs.edit().putString("macIp", macIp).apply();
            }
        });
        status = new TextView(this);
        status.setTextSize(18);
        status.setPadding(0, 48, 0, 0);
        layout.addView(label);
        layout.addView(ipField);
        layout.addView(status);
        setContentView(layout);

        net.execute(() -> {
            try {
                socket = new DatagramSocket();
                socket.setBroadcast(true);
            } catch (Exception e) {
                state = "UDP socket failed: " + e;
            }
        });
        refreshStatus();

        connectIQ = ConnectIQ.getInstance(this, ConnectIQ.IQConnectType.WIRELESS);
        connectIQ.initialize(this, true, new ConnectIQ.ConnectIQListener() {
            @Override public void onSdkReady() { registerDevices(); }
            @Override public void onInitializeError(ConnectIQ.IQSdkErrorStatus error) {
                state = "Connect IQ error: " + error + " (is Garmin Connect installed?)";
            }
            @Override public void onSdkShutDown() { state = "Connect IQ shut down"; }
        });
    }

    private void registerDevices() {
        try {
            List<IQDevice> devices = connectIQ.getKnownDevices();
            if (devices == null || devices.isEmpty()) {
                state = "No Garmin devices paired in Garmin Connect";
                return;
            }
            for (IQDevice device : devices) {
                connectIQ.registerForDeviceEvents(device, (d, s) -> {
                    state = d.getFriendlyName() + ": " + s;
                    if (s == IQDevice.IQDeviceStatus.CONNECTED) listenTo(d);
                });
                listenTo(device);
            }
        } catch (Exception e) {
            state = "Could not list devices: " + e;
        }
    }

    private void listenTo(IQDevice device) {
        try {
            connectIQ.registerForAppEvents(device, watchApp, (d, app, messages, s) -> {
                if (s != ConnectIQ.IQMessageStatus.SUCCESS) return;
                for (Object message : messages) relay(String.valueOf(message));
            });
            state = "Listening to " + device.getFriendlyName();
        } catch (Exception e) {
            state = "Could not listen to " + device.getFriendlyName() + ": " + e;
        }
    }

    private void relay(String message) {
        net.execute(() -> {
            if (socket == null) return;
            try {
                String target = macIp.isEmpty() ? "255.255.255.255" : macIp;
                byte[] bytes = message.getBytes(StandardCharsets.US_ASCII);
                socket.send(new DatagramPacket(bytes, bytes.length, InetAddress.getByName(target), PORT));
                relayed++;
                lastMessage = message;
            } catch (Exception e) {
                state = "Send failed: " + e.getMessage();
            }
        });
    }

    private void refreshStatus() {
        status.setText(state + "\n\nRelayed: " + relayed + "\nLast: " + lastMessage);
        ui.postDelayed(this::refreshStatus, 250);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        ui.removeCallbacksAndMessages(null);
        try {
            connectIQ.unregisterAllForEvents();
            connectIQ.shutdown(this);
        } catch (Exception ignored) {
        }
        net.execute(() -> { if (socket != null) socket.close(); });
        net.shutdown();
    }
}
