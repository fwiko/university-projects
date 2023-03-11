package loadbalancer.managers;

import java.util.LinkedHashMap;
import java.util.LinkedList;
import java.util.stream.Collectors;
import loadbalancer.job.Job;
import loadbalancer.node.Node;

public class JobManager {
    // Value holding the singleton instance of the Job Manager
    private static JobManager instance = null;
    
    // LinkedList used to queue Jobs in FIFO (First-In, First-Out) order
    private LinkedList<Job> jobQueue = null;
    
    // LinkedHashMap used to pair Jobs to their "handler" Nodes
    private LinkedHashMap<Job, Node> jobAllocations = null;
    
    // Mutex objects used to allow exclusive access to the "jobQueue" LinkedList and "jobAllocations" LinkedHashMap
    private final Object jobQueueMutex = new Object();
    private final Object jobAllocationsMutex = new Object();

    // Next Job ID Number to assign to a Job when one is created
    private int nextJobIdNumber = 1;
    
    private JobManager() {
        this.jobQueue = new LinkedList<>();
        this.jobAllocations = new LinkedHashMap<>();
    }
    
    public static JobManager getInstance() {
        // If there is no current instance of the Job Manager, create a new Instance
        if (instance == null) {
            instance = new JobManager();
        }
        
        return instance;
    }
    
    public Job addNewJob(int executionTime) {
        // Create a new Job object with the next Job ID Number and given Execution Time
        Job job = new Job(nextJobIdNumber, executionTime);
        
        // Add the new Job object to the Job queue
        queueJob(job);
        
        // Increment the next Job ID Number value by 1
        nextJobIdNumber += 1;
        
        return job;
    }
    
    public void queueJob(Job job) {
        // Aquire the "jobQueueMutex" Mutex and add the given Job to the "jobQueue" LinkedList
        synchronized (jobQueueMutex) {
            jobQueue.add(job);
        }
        
        System.out.printf("JobManager - INFO: Job %d has been added to the queue\n", job.getIdNumber());
    }
    
    public void allocateJob(Job job, Node node) {
        // Aquire the "jobQueueMutex" Mutex and remove the given Job from the "jobQueue" LinkedList
        synchronized (jobQueueMutex) {
            jobQueue.remove(job);
        }
        
        // Aquire the "jobAllocationsMutex" Mutex and add a new allocation record to the "jobAllocations" LinkedHashMap
        synchronized (jobAllocationsMutex) {
            jobAllocations.put(job, node);
        }
        
        System.out.printf("JobManager - INFO: Allocated Job %d to Node %d (now at %s%% usage)\n", job.getIdNumber(), node.getIdNumber(), String.format("%.2f", node.getCurrentUsage()));
    }
    
    public void deallocateJob(Job job) {
        Node handlerNode = null;
        
        // Aquire the "jobAllocationsMutex" Mutex
        synchronized (jobAllocationsMutex) {
            // Retreive the Node value under the given Job key
            handlerNode = jobAllocations.get(job);
            
            // Remove the allocation record from the "jobAllocations" LinkedHashMap
            jobAllocations.remove(job);
        }
        
        System.out.printf("JobManager - INFO: Deallocated Job %d from Node %d\n", job.getIdNumber(), handlerNode.getIdNumber());
    }
    
    public Job getAllocatedJobById(int idNumber) {
        // Aquire the "jobAllocationsMutex" Mutex
        synchronized (jobAllocationsMutex) {
            // Return the first Job object with a matching ID Number
            for (Job job : jobAllocations.keySet()) {
                if (job.getIdNumber() == idNumber) { return job; }
            }
        }
        
        return null;
    }
    
    public Job getNextQueuedJob() {
        // Aquire the "jobQueueMutex" Mutex
        synchronized (jobQueueMutex) {
            // Get/return (without removing) the first element of the "jobQueue" LinkedList
            return jobQueue.peekFirst();
        }
    }
    
    public LinkedList<Job> getNodeJobs(Node node) {
        // Aquire the "jobAllocationsMutex" Mutex
        synchronized (jobAllocationsMutex) {
            // Return a LinkedList containing all Jobs allocated to the given Node
            return jobAllocations.keySet()
                    .stream()
                    .filter(job -> jobAllocations.get(job) == node)
                    .collect(Collectors.toCollection(LinkedList<Job>::new));
        }
    }
    
    public LinkedList<Job> getJobQueue() {
        // Aquire the "jobQueueMutex" Mutex
        synchronized (jobQueueMutex) {
            // Return the "jobQueue" LinkedList
            return jobQueue;
        }
    }
    
    public LinkedHashMap<Job, Node> getAllocatedJobs() {
        // Aquire the "jobAllocationsMutex" Mutex
        synchronized (jobAllocationsMutex) {
            // Return the "jobAllocations" LinkedHashMap
            return jobAllocations;
        }
    }
}
