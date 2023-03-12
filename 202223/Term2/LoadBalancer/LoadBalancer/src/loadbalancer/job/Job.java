package loadbalancer.job;

public class Job {
    // Job details (Job ID Number is unique)
    private int idNumber = -1;
    private int executionTime = -1;
    
    public Job(int idNumber, int executionTime) {
        this.idNumber = idNumber;
        this.executionTime = executionTime;
    }
    
    public int getIdNumber() {
        return idNumber;
    }
    
    public int getExecutionTime() {
        return executionTime;
    }
}
