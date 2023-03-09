package node.job;

public class Job {
    private JobStatus status = null;
    
    private int idNumber = -1;
    private int executionTime = -1;
    
    private Thread jobThread = null;
    
    public Job(int idNumber, int executionTime) {
        this.idNumber = idNumber;
        this.executionTime = executionTime;
    }    
    
    public void start() {
        jobThread = new Thread() {
            @Override
            public void run() {
                status = JobStatus.RUNNING;
                try {
                    Thread.sleep(executionTime * 1000);
                } catch (InterruptedException exception) {
                    status = JobStatus.INTERRUPTED;
                    return;
                }
                status = JobStatus.FINISHED;
            }
        };
        
        jobThread.start();
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
    
    public void stop() {
        jobThread.interrupt();
    }
}
