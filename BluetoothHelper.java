package org.bluetoothproject.bluetoothsender;

import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanResult;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCallback;
import android.bluetooth.BluetoothGattCharacteristic;

public class BluetoothHelper {

public static abstract class Scanner extends ScanCallback {
    public abstract void onDeviceFound(ScanResult result);
    public abstract void onScanError(int error);

    @Override
    public void onScanResult(int callbackType, ScanResult result) {
        onDeviceFound(result);
    }

    @Override
    public void onScanFailed(int errorCode) {
        onScanError(errorCode);
    }
}

public static abstract class Gatt extends BluetoothGattCallback {
    public abstract void onConnection(BluetoothGatt gatt, int status, int state);
    public abstract void onServices(BluetoothGatt gatt, int status);
    public abstract void onWrite(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic, int status);

    @Override
    public void onConnectionStateChange(BluetoothGatt gatt, int status, int newState) {
        onConnection(gatt, status, newState);
    }

    @Override
    public void onServicesDiscovered(BluetoothGatt gatt, int status) {
        onServices(gatt, status);
    }

    @Override
    public void onCharacteristicWrite(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic, int status) {
        onWrite(gatt, characteristic, status);
    }
}

}
