
package node.managers;

import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.StandardProtocolFamily;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.util.LinkedList;
import node.messages.MessageInbound;
import node.messages.MessageOutbound;

public class MessageManager {
    private static MessageManager instance = null;
    
    private Thread messageReceiver = null;
    
    private DatagramChannel datagramChannel = null;
    
    private LinkedList<MessageInbound> messageQueue = null;
    
    private final Object messageQueueMutex = new Object();
    
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
    
    public void sendMessage(MessageOutbound message, InetAddress ipAddress, int portNumber) {
        ByteBuffer buffer = ByteBuffer.wrap(message.packString().getBytes());
        
        try {
            datagramChannel.send(buffer, new InetSocketAddress(ipAddress, portNumber));
        } catch (IOException exception) {
            System.err.printf("MessageManager - ERROR: Failed to send %s Message to socket %s:%d", message.getType(), ipAddress.getHostAddress(), portNumber);
            return;
        }
        
        System.out.printf("MessageManager - INFO: Sent %s Message to socket %s:%d\n", message.getType(), ipAddress.getHostAddress(), portNumber);
    }
    
    public void stop() {
        messageReceiver.interrupt();
    }
    
    public boolean isStopped() {
        return messageReceiver.isInterrupted();
    }
    
    private void receive() {
        messageReceiver = new Thread() {
            @Override
            public void run() {
                System.out.printf("MessageManager - INFO: Listening for Messages on Socket %s:%s\n",datagramChannel.socket().getLocalAddress().getHostAddress(), datagramChannel.socket().getLocalPort());
                
                while (!interrupted()) {
                    ByteBuffer buffer = ByteBuffer.allocate(1024);
                    
                    try {
                        datagramChannel.receive(buffer);
                    } catch (IOException exception) {
                        messageReceiver.interrupt();
                        break;
                    }
                    
                    String messageString = new String(buffer.array()).trim();
                    
                    if (messageString.isEmpty()) {
                        continue;
                    }
                    
                    queueMessage(new MessageInbound(messageString));
                    
                    System.out.printf("MessageManager - INFO: Received %s Message\n", "");
                }
            }
        };
        
        messageReceiver.start();
    }
    
    private void queueMessage(MessageInbound message) {
        synchronized (messageQueueMutex) {
            messageQueue.add(message);
        }
    }
    
    public MessageInbound getNextQueuedMessage() {
        synchronized (messageQueueMutex) {
            return messageQueue.pollFirst();
        }
    }
}
