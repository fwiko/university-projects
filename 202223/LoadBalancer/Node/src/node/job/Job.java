package node.job;

public class Job {
    // status of the Job - One of the three JobStatus Enumerator values
    private JobStatus status = null;
    
    // Job details holding the specific Job ID Number and Execution time
    private int idNumber = -1;
    private int executionTime = -1;
    
    // Thread used to do the "work" without blocking Node execution
    private Thread jobThread = null;
    
    public Job(int idNumber, int executionTime) {
        this.idNumber = idNumber;
        this.executionTime = executionTime;
    }    
    
    public void start() {
        // Create a new Thread used to do the "work" received from the Load-Balancer
        jobThread = new Thread() {
            @Override
            public void run() {
                // Set the Job object's status to RUNNING
                status = JobStatus.RUNNING;
                
                // Do the "work" (wait for the specified execution time in milliseconds)
                try {
                    Thread.sleep(executionTime * 1000);
                } catch (InterruptedException exception) { // Handle an InterruptedException if the Thread is Interrupted and set status to INTERRUPTED
                    status = JobStatus.INTERRUPTED;
                    return;
                }
                
                // Set the Job object's status to FINISHED when the "work" has complete
                status = JobStatus.FINISHED;
            }
        };
        
        // Start the above "jobThread" Thread
        jobThread.start();
    }
    
    public void stop() {
        // Interrupt (stop) the Job Execution Thread ("jobThread") - stopping any work
        jobThread.interrupt();
    }
    
    public JobStatus getStatus() {
        return status;
    }
    
    public int getIdNumber() {
        return idNumber;
    }
    
    public int getExecutionTime() {
        return executionTime;
    }

}
