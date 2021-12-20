import os
import shlex
from subprocess import Popen, PIPE
import jinja2
import time
import sys


def get_exitcode_stdout_stderr(cmd):
	# Execute the external command and get its exitcode, stdout and stderr.
	args = shlex.split(cmd)
	proc = Popen(args, stdout=PIPE, stderr=PIPE)
	proc.wait()
	out, err = proc.communicate()
	exitcode = proc.returncode
	return exitcode, out, err


def get_service_node_names():
	c, out, err = get_exitcode_stdout_stderr("kubectl get nodes")
	names = []
	dispatcher_node = ""
	for line in out.decode('ascii').split("\n"):
		splits = line.split()
		if len(splits) < 5: break
		if "nodes" in splits[0]:  # check name is nodes-...
			names.append(splits[0])
		elif "cachew-dispatcher-" in splits[0]:
			dispatcher_node = splits[0]
	return dispatcher_node, names


def kubectrl_apply(yaml_file_name):
	get_exitcode_stdout_stderr(f"kubectl apply -f {yaml_file_name}")
	while not (check_service_interfaces_up()):
		time.sleep(1)


def check_service_interfaces_up():
	c, out, err = get_exitcode_stdout_stderr("kubectl get services")
	for line in out.decode('ascii').split("\n"):
		splits = line.split()
		if len(splits) < 5: break
		if "data-service-" in splits[0]:
			if "<pending>" in splits[3]:
				return False
	return True


def check_service_ready():
	c, out, err = get_exitcode_stdout_stderr("kubectl get pods")
	for line in out.decode('ascii').split("\n"):
		splits = line.split()
		if len(splits) < 5: break
		if "node-exporter-" in splits[0]:
			if not ("Running" in splits[2] and "1/1" in splits[1]):
				return False
	return True


def gen_yaml(yaml_file_name, **kwargs):
	with open(f"{yaml_file_name}.jinja", "r") as source:
		yaml = jinja2.Template(source.read()).render(**kwargs)
	with open(yaml_file_name, "w") as destination:
		destination.write(yaml)


def start_service():
	print("Creating kubernetes service...")

	dispatcher_node, worker_nodes = get_service_node_names()
	dispatcher = {'ip': dispatcher_node, 'port': 32000}
	workers = []
	for i in range(len(worker_nodes)):
		w = {"index": i, 'port': dispatcher['port'] + i + 1}
		workers.append(w)
	for worker_node, worker in zip(worker_nodes, workers):
		worker["ip"] = worker_node
		worker["name"] = "node-exporter-worker-" + str(worker["index"])

	gen_yaml('kubernetes/node_exporter_interfaces.yaml', dispatcher=dispatcher, workers=workers)
	kubectrl_apply('kubernetes/node_exporter_interfaces.yaml')

	gen_yaml('kubernetes/node_exporter.yaml', dispatcher=dispatcher, workers=workers)
	kubectrl_apply('kubernetes/node_exporter.yaml')
	print("Created kubernetes service.")

	gen_yaml('prometheus2/prometheus-config/prometheus.yml', dispatcher=dispatcher, workers=workers)


def stop_service():
	print("Stopping services")
	c, out, err = get_exitcode_stdout_stderr("kubectl get services")

	names = []
	for line in out.decode('ascii').split("\n"):
		splits = line.split()
		if len(splits) < 5: break
		if "node-exporter-" in splits[0]:
			names.append(splits[0])

	for name in names:
		get_exitcode_stdout_stderr("kubectl delete rs " + name)
		get_exitcode_stdout_stderr("kubectl delete service " + name)

	print("Stopped services")


def start_docker():
	os.chdir('prometheus2')
	get_exitcode_stdout_stderr('docker-compose up -d')
	os.chdir('..')


def stop_docker():
	os.chdir('prometheus2')
	get_exitcode_stdout_stderr('docker-compose down')
	os.chdir('..')


def main(stop=False):
	stop_docker()
	stop_service()
	if not stop:
		start_service()
		start_docker()


if __name__ == '__main__':
	main(len(sys.argv) > 1)

