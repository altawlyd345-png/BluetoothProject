package org.bluetoothproject.bluetoothsender;

import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanResult;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCallback;
import android.bluetooth.BluetoothGattCharacteristic;

public class BluetoothHelper {

public interface ScanListener {
    void onDeviceFound(ScanResult result);
    void onScanError(int error);
}

public interface GattListener {
    void onConnection(BluetoothGatt gatt, int status, int state);
    void onServices(BluetoothGatt gatt, int status);
    void onWrite(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic, int status);
}

public static ScanCallback createScanner(final ScanListener listener) {
    return new ScanCallback() {
        @Override
        public void onScanResult(int callbackType, ScanResult result) {
            listener.onDeviceFound(result);
        }

        @Override
        public void onScanFailed(int errorCode) {
            listener.onScanError(errorCode);
        }
    };
}

public static BluetoothGattCallback createGattCallback(final GattListener listener) {
    return new BluetoothGattCallback() {
        @Override
        public void onConnectionStateChange(BluetoothGatt gatt, int status, int newState) {
            listener.onConnection(gatt, status, newState);
        }

        @Override
        public void onServicesDiscovered(BluetoothGatt gatt, int status) {
            listener.onServices(gatt, status);
        }

        @Override
        public void onCharacteristicWrite(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic, int status) {
            listener.onWrite(gatt, characteristic, status);
        }
    };
}

}
