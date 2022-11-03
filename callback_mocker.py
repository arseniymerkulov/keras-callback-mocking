from capturemock import RECORD, REPLAY
import inspect
import json


class CallbackMocker:
    def __init__(self):
        self.save_path = 'capturemock/callbacks.json'
        self.callbacks = []

    def add_callback_signature(self, callback_type, args, kwargs, callback_code, callback_output_name):
        # take out 'self' argument
        args = args[1:]

        # take out decorators and method definition and return lines
        lines = callback_code.split('\n')

        definition_line = list(filter(lambda x: 'def ' in x, lines))[0]
        arg_names = definition_line.split('(', 1)[1].replace('):', '').replace(' ', '')
        arg_names = arg_names.split(',')
        arg_names = [arg_name.split('=')[0] for arg_name in arg_names if arg_name != 'self']

        return_lines = list(filter(lambda x: 'return ' in x, lines))

        for return_line in return_lines:
            i = lines.index(return_line)
            lines[i] = lines[i].replace('return ', f'{callback_output_name} = ')

        lines = [line + '\n' for line in lines if '@' not in line and 'def ' not in line]

        indent = lines[0].split(' ')[0] + ' '
        lines = [line.replace(indent, '') for line in lines]

        callback_code = ''.join(lines)

        self.callbacks.append({
            'callback_type': callback_type,
            'arg_names': arg_names,
            'args': args,
            'kwargs': kwargs,
            'callback_code': callback_code
        })

    def save_callback_signatures(self):
        with open(self.save_path, 'w') as file:
            file.write(json.dumps(self.callbacks))

    def eval_callback_signatures(self, callback_output_name, callback_output):
        with open(self.save_path, 'r') as file:
            callbacks = json.loads(file.read())

            for callback in callbacks:
                CallbackMocker.eval_callback_signature(callback, callback_output_name, callback_output)

    @staticmethod
    def eval_callback_signature(callback, callback_output_name, callback_output):
        arguments = {}

        args = callback['args']
        kwargs = list(callback['kwargs'].values())

        for i, key in enumerate(callback['arg_names']):
            if i < len(args):
                arguments[key] = args[i]
            else:
                arguments[key] = kwargs[i - len(args)]

        local = {}

        exec(callback['callback_code'], arguments, local)
        callback_output.append(local[callback_output_name])


def callbackmock(callback_mocker: CallbackMocker, callback_output_name, callback_output):
    def decorator(callback):
        def wrapper(*args, **kwargs):
            callback_mocker.add_callback_signature(callback.__name__,
                                                   args,
                                                   kwargs,
                                                   inspect.getsource(callback),
                                                   callback_output_name)
            callback_output.append(callback(*args, **kwargs))

        return wrapper

    return decorator


def callbackmocker(callback_mocker: CallbackMocker, callback_output_name, callback_output, mode):
    def decorator(callback):
        def wrapper(*args, **kwargs):
            if mode == RECORD:
                callback(*args, **kwargs)
                callback_mocker.save_callback_signatures()
            elif mode == REPLAY:
                callback_mocker.eval_callback_signatures(callback_output_name, callback_output)
                callback(*args, **kwargs)

        return wrapper

    return decorator
