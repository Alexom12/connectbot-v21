package com.connectbot.matching.client;

public class DataApiException extends RuntimeException {
    private int statusCode = -1;

    public DataApiException(String message) {
        super(message);
    }

    public DataApiException(String message, int statusCode) {
        super(message);
        this.statusCode = statusCode;
    }

    public int getStatusCode() {
        return statusCode;
    }
}
