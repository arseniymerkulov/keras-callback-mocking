from capturemock import capturemock, RECORD, REPLAY
from callback_mocker import CallbackMocker, callbackmock, callbackmocker


callback_mocker = CallbackMocker()
callback_output = []
mode = RECORD


class Model:
    def __init__(self):
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Dense

        self.num_classes = 10
        self.input_shape = (1, 784)

        self.model = Sequential()
        self.model.add(Dense(800, input_dim=self.input_shape[1], activation='relu'))
        self.model.add(Dense(100, activation='relu'))
        self.model.add(Dense(self.num_classes, activation='softmax'))
        self.model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    def get_dataset(self):
        from tensorflow.keras.datasets import mnist
        from tensorflow.keras import utils

        (x_train, y_train), (x_test, y_test) = mnist.load_data()

        x_train = x_train.reshape(x_train.shape[0], -1)
        x_train = x_train.astype('float32') / 255.
        y_train = utils.to_categorical(y_train, self.num_classes)

        return x_train, y_train

    def fit(self):
        from tensorflow.keras.callbacks import Callback

        class FitCallback(Callback):
            @callbackmock(callback_mocker, 'callback_output', callback_output)
            def on_train_end(self, logs=None):
                print(logs)
                return logs

            @callbackmock(callback_mocker, 'callback_output', callback_output)
            def on_epoch_end(self, epoch, logs=None):
                print(logs)
                return logs

        x_train, y_train = self.get_dataset()
        history = self.model.fit(x_train,
                                 y_train,
                                 callbacks=[FitCallback()],
                                 batch_size=128,
                                 epochs=15,
                                 verbose=1)

        history = history.__dict__
        history['model'] = None

        return history


def general_fit_function():
    model = Model()
    history = model.fit()

    return history


@callbackmocker(callback_mocker, 'callback_output', callback_output, mode)
@capturemock('__main__.general_fit_function', mode=mode)
def test_training():
    history = general_fit_function()

    metrics = list(history['history'].keys())
    params = list(history['params'].values())
    on_train_end = callback_output[-1]

    print(callback_output)
    print(metrics)
    print(params)

    # for some reason capturemock serialization\deserialization process goes other way
    # and dict keys swap places in REPLAY and RECORD modes
    assert 'loss' in metrics and 'accuracy' in metrics
    assert 1 in params and 15 in params and 469 in params
    assert 'loss' in on_train_end and 'accuracy' in on_train_end


if __name__ == '__main__':
    test_training()
