package loadbalancer.managers;

import java.io.IOException;
import static java.lang.Thread.interrupted;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.StandardProtocolFamily;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.util.LinkedList;
import loadbalancer.messages.MessageInbound;
import loadbalancer.messages.MessageOutbound;

public class MessageManager {
    private static MessageManager instance;
    private Thread messageReceiver = null;
    private boolean running = false;
    private DatagramChannel datagramChannel = null;
    private final LinkedList<MessageInbound> messageQueue;
    private final Object messageQueueLock = new Object();
    
    private MessageManager() {
        messageQueue = new LinkedList<>();
    }

    public static MessageManager getInstance() {
        if (instance != null) {
            return instance;
        }
        instance = new MessageManager();
        return instance;
    }
    
    public void start(InetAddress ipAddress, int portNumber) throws IOException {
        datagramChannel = DatagramChannel.open(StandardProtocolFamily.INET)
                .bind(new InetSocketAddress(ipAddress, portNumber));
        datagramChannel.configureBlocking(false);
        receive();
    }

    private void receive() {
        messageReceiver = new Thread() {
            @Override
            public void run() {
                running = true;
                System.out.printf("Message Manager (Info): Listening for Messages on socket %s:%d\n", datagramChannel.socket().getLocalAddress().getHostAddress(), datagramChannel.socket().getLocalPort());
                while (!interrupted()) {
                    ByteBuffer buffer = ByteBuffer.allocate(1024);
                    try {
                        datagramChannel.receive(buffer);
                    } catch (IOException e) {
                        System.err.println("Message Manager (Error): IOException when receiving Message(s)");
                        messageReceiver.interrupt();
                        running = false;
                        break;
                    }
                    String messageString = new String(buffer.array()).trim();
                    if (!messageString.isEmpty()) {
                        MessageInbound newMessage = new MessageInbound(messageString);
                        System.out.printf("Message Manager (Info): Received new %s Message\n", newMessage.getType().toString());
                        queueMessage(newMessage);
                    }
                }
            }
        };
        messageReceiver.start();
    }

    public void sendMessage(MessageOutbound message, InetAddress ipAddress, int portNumber){
        byte[] messageBytes = message.packString().getBytes();
        ByteBuffer buffer = ByteBuffer.wrap(messageBytes);
        try {
            datagramChannel.send(buffer, new InetSocketAddress(ipAddress, portNumber));
        } catch (IOException e) {
            System.err.printf("Message Manager (Info): Failed to send %s Message to socket %s:%d\n", message.getType().toString(), ipAddress.getHostAddress(), portNumber);
            return;
        }
        System.out.printf("Message Manager (Info): Sent %s Message to socket %s:%d\n", message.getType().toString(), ipAddress.getHostAddress(), portNumber);
    }

    private void queueMessage(MessageInbound message) {
        synchronized (messageQueueLock) {
            messageQueue.add(message);
        }
    }

    public MessageInbound getNextMessage() {
        synchronized (messageQueueLock) {
            return messageQueue.poll();
        }
    }

    public void stop() {
        messageReceiver.interrupt();
        running = false;
    }
    
    public boolean isStopped() {
        return messageReceiver.isInterrupted() || !running;
    }
}