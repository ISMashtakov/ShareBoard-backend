import threading
import os
import traceback

import pexpect

from helpers.logger import create_logger


FILE_PATH = '/home/username/Code_Docs/running_files/'
DOCKER_IMAGES = {'python': 'code_docs_python'}


run_file_logger = create_logger("run_file_logger")


class RunFileThread(threading.Thread):
    def __init__(self, file_name, file_content, programming_language, consumer=1):
        super().__init__(name="run file")
        self.filename = self.create_file(file_name, file_content)
        self.docker_image = DOCKER_IMAGES[programming_language]
        self.consumer = consumer
        self.inputs = []
        self.__close_force = False

    def create_file(self, file_name, file_content):
        generated_filename = FILE_PATH + file_name

        if not os.path.exists(FILE_PATH):
            os.makedirs(FILE_PATH)

        with open(generated_filename, 'w') as file:
            file.write(file_content)

        return generated_filename

    def delete_file(self):
        try:
            run_file_logger.info("delete_file")
            os.remove(self.filename)
        except OSError:
            run_file_logger.info("file was deleted")
            pass

    def add_input(self, file_input):
        run_file_logger.info(f"ADD INPUT {file_input}")
        self.inputs.append(file_input)
        run_file_logger.info(f"INPUTS NOW {self.inputs}")

    def run(self) -> None:
        run_file_logger.info("start RunFileThread")
        command = f'docker run ' \
                  f'--mount type=bind,source={self.filename},destination=/root/my_file,readonly ' \
                  f'--rm -it {self.docker_image}'

        child = pexpect.spawn(command, encoding='utf-8')
        child.timeout = 1
        child.delimiter = pexpect.TIMEOUT
        try:
            while True:
                # force process to stop
                if self.__close_force:
                    run_file_logger.info("force close child")
                    child.close(force=True)
                    break

                if self.inputs:
                    run_file_logger.info(f"before send input - {self.inputs[-1]}")
                    child.sendline(self.inputs.pop(0))

                try:
                    output = child.readline()
                    if child.after == pexpect.TIMEOUT:
                        # run_file_logger.info("in if")
                        output = child.read(len(child.before))
                    if output:
                        self.consumer.file_output(output)
                except Exception as exc:
                    run_file_logger.error(f"{__name__} {exc} {traceback.format_exc()}")

                if not child.isalive():
                    if child.before:
                        self.consumer.file_output(child.before)
                    break
        except Exception as exc:
            run_file_logger.error(f"123 {__name__} {exc} {traceback.format_exc()}")
            self.consumer.file_output("Your time is over")
            child.close(force=True)
        finally:
            self.consumer.send_to_group({'type': 'END run_file', 'exit_code': child.exitstatus})
            self.consumer.launched_file_manager.remove_stopped_file(self.consumer.file.pk)
            self.delete_file()

    def close(self):
        self.__close_force = True
