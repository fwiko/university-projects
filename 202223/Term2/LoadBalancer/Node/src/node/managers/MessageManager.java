package node.managers;

import java.io.IOException;
import static java.lang.Thread.interrupted;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.StandardProtocolFamily;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.util.LinkedList;
import node.messages.MessageInbound;
import node.messages.MessageOutbound;

public class MessageManager {
    // Singleton instance of MessageManager
    private static MessageManager instance;
    
    // Thread used to receive Messages - to stop blocking
    private Thread messageReceiver = null;
    
    // DatagramChannel to send and receive datagram packets
    private DatagramChannel datagramChannel = null;
    
    // LinkedList of received Message objects yet to be handled
    private final LinkedList<MessageInbound> messageQueue;
    
    // Mutex object used for exclusive access to the messageQueue LinkedList
    private final Object messageQueueLock = new Object();
    
    private MessageManager() {
        messageQueue = new LinkedList<>();
    }

    public static MessageManager getInstance() {
        // If an instance of the MessageManager already exists
        if (instance != null) {
            return instance;
        }
        // Create a new instance of the MessageManager
        instance = new MessageManager();
        return instance;
    }
    
    public void start(InetAddress ipAddress, int portNumber) throws IOException {
        // Open the DatagramChannel and bind to the specified IP Address and Port Number of the Node
        datagramChannel = DatagramChannel.open(StandardProtocolFamily.INET)
                .bind(new InetSocketAddress(ipAddress, portNumber));
        // Set the DatagramChannel to non-blocking
        datagramChannel.configureBlocking(false);
        
        // Begin to receive Messages from the Load-Balancer
        receive();
    }

    private void receive() {
        messageReceiver = new Thread() {
            @Override
            public void run() {
                
                System.out.printf("MessageManager - INFO: Listening for Messages on socket %s:%s\n", datagramChannel.socket().getLocalAddress().getHostAddress(), datagramChannel.socket().getLocalPort());
                
                //
                while (!interrupted()) {
                    // ByteBuffer object used to store up to 1024 Bytes of data (similar to byte[])
                    ByteBuffer buffer = ByteBuffer.allocate(1024);
                    
                    // Receive incoming Messages through the DatagramChannel and write their contents to the buffer
                    try {
                        datagramChannel.receive(buffer);
                    } catch (IOException e) {
                        System.out.println("MessageManager - ERROR: IOException when receiving Message");
                        messageReceiver.interrupt();
                        break;
                    }
                    
                    //
                    String messageString = new String(buffer.array()).trim();
                    if (!messageString.isEmpty()) {
                        //
                        MessageInbound newMessage = new MessageInbound(messageString);
                        
                        System.out.printf("MessageManager - INFO: Received %s Message\n", newMessage.getType().toString());
                        
                        //
                        queueMessage(newMessage);
                    }
                }
            }
        };
        messageReceiver.start();
    }

    public void sendMessage(MessageOutbound message, InetAddress ipAddress, int portNumber){
        // Pack the Message object into a String, Encode the String as Bytes and store in the BytesBuffer buffer
        ByteBuffer buffer = ByteBuffer.wrap(message.packString().getBytes());
        
        // Attempt to send the Message across the DatagramChannel datagramChannel to the specified IP Address and Port Number (Load-Balancer)
        try {
            datagramChannel.send(buffer, new InetSocketAddress(ipAddress, portNumber));
        } catch (IOException e) {
            System.err.printf("MessageManager - ERROR: Failed to send %s Message to socket %s:%d\n", message.getType().toString(), ipAddress.getHostAddress(), portNumber);
            return;
        }
        
        System.out.printf("MessageManager - INFO: Sent %s Message to socket %s:%d\n", message.getType().toString(), ipAddress.getHostAddress(), portNumber);
    }

    private void queueMessage(MessageInbound message) {
        //
        synchronized (messageQueueLock) {
            //
            messageQueue.add(message);
        }
    }

    public MessageInbound getNextMessage() {
        //
        synchronized (messageQueueLock) {
            //
            return messageQueue.poll();
        }
    }

    public void stop() {
        // 
        messageReceiver.interrupt();
    }
    
    public boolean isStopped() {
        //
        return messageReceiver.isInterrupted();
    }
}