package node.job;

public class Job {
    //
    private int idNumber = -1;
    private int executionTime = -1;
    private JobStatus status = null;
    
    //
    private Thread workThread = null;
    
    public Job(int idNumber, int executionTime) {
        this.idNumber = idNumber;
        this.executionTime = executionTime;
    }
    
    public void start() {
        workThread = new Thread() {
            @Override
            public void run() {
                status = JobStatus.RUNNING;
                try {
                    Thread.sleep(executionTime * 1000);
                } catch (InterruptedException e) {
                    status = JobStatus.INTERRUPTED;
                }
                status = JobStatus.FINISHED;
            }
        };
        workThread.start();
    }
    
    public int getIdNumber() {
        return idNumber;
    }
    
    public int getExecutionTime() {
        return executionTime;
    }
    
    public JobStatus getStatus() {
        return status;
    }
    
    public void stop() {
        //
        workThread.interrupt();
    }
}
