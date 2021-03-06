from config.api1_1_config import *
from config.settings import *
from modules.logger import Log
from on_http_api1_1 import NodesApi as Nodes
from on_http_api1_1 import rest
from workflows_tests import WorkflowsTests as workflows
from datetime import datetime
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_false
from proboscis.asserts import assert_raises
from proboscis.asserts import assert_true
from proboscis.asserts import assert_not_equal
from proboscis.asserts import assert_is_not_none
from proboscis import SkipTest
from proboscis import test
from proboscis import after_class
from proboscis import before_class
from proboscis.asserts import fail
from json import dumps, loads, load
import os

LOG = Log(__name__)
DEFAULT_TIMEOUT_SEC = 5400
ENABLE_FORMAT_DRIVE=False
if os.getenv('RACKHD_ENABLE_FORMAT_DRIVE', 'false') == 'true': 
    ENABLE_FORMAT_DRIVE=True

@test(groups=['os-install.v1.1.tests'], \
    depends_on_groups=['amqp.tests'])
class OSInstallTests(object):

    def __init__(self):
        self.__client = config.api_client
        self.__base = defaults.get('RACKHD_BASE_REPO_URL', \
            'http://{0}:{1}'.format(HOST_IP, HOST_PORT))
        self.__obm_options = { 
            'obmServiceName': defaults.get('RACKHD_GLOBAL_OBM_SERVICE_NAME', \
                'ipmi-obm-service')
        }
        self.__sampleDir = defaults.get('RACKHD_SAMPLE_PAYLOADS_PATH', \
            '../example/samples/')

    @before_class()
    def setup(self):
        pass
        
    @after_class(always_run=True)
    def teardown(self):
        self.__format_drives()  
    
    def __get_data(self):
        return loads(self.__client.last_response.data)
    
    def __post_workflow(self, graph_name, nodes, body):
        workflows().post_workflows(graph_name, timeout_sec=DEFAULT_TIMEOUT_SEC, nodes=nodes, data=body)         

    def __format_drives(self):
        # Clear disk MBR and partitions
        command = 'for disk in `lsblk | grep disk | awk \'{print $1}\'`; do '
        command = command + 'sudo dd if=/dev/zero of=/dev/$disk bs=512 count=1 ; done'
        body = {
            'options': {
                'shell-commands': {
                    'commands': [ 
                        { 'command': command } 
                    ]
                },
                'set-boot-pxe': self.__obm_options,
                'reboot-start': self.__obm_options,
                'reboot-end': self.__obm_options
            }
        }
        self.__post_workflow('Graph.ShellCommands', [], body)

    def __get_os_install_payload(self, payload_file_name, os_repo):
        payload = open(self.__sampleDir  + payload_file_name, 'r')
        body = load(payload)
        payload.close()
        if body != None:
            body['options']['defaults']['repo'] = os_repo
        return body

    @test(enabled=ENABLE_FORMAT_DRIVE, groups=['format-drives.v1.1.test'])
    def test_format_drives(self):
        """ Drive Format Test """
        self.__format_drives()  
        
    def install_centos(self, version, nodes=[], options=None):
        graph_name = 'Graph.InstallCentOS'
        os_repo = defaults.get('RACKHD_CENTOS_REPO_PATH', \
            self.__base + '/repo/centos/{0}'.format(version))
        body = options
        if body == None:
            body = {
                'options': {
                    'defaults': {
                        'installDisk': '/dev/sda',
                        'version': version,
                        'repo': os_repo,
			'users': [{ 'name': 'onrack', 'password': 'Onr@ck1!', 'uid': 1010 }]
                    },
                    'set-boot-pxe': self.__obm_options,
                    'reboot': self.__obm_options,
                    'install-os': {
                        'schedulerOverrides': {
                            'timeout': 3600000
                        }
                    }
                }
            } 
        self.__post_workflow(graph_name, nodes, body)
        
    def install_esxi(self, version, nodes=[], options=None):
        graph_name = 'Graph.InstallESXi'
        os_repo = defaults.get('RACKHD_ESXI_REPO_PATH', \
            self.__base + '/repo/esxi/{0}'.format(version))
        body = options
        if body == None:
            body = {
                'options': {
                    'defaults': {
                        'installDisk': 'firstdisk',
                        'version': version, 
                        'repo': os_repo,
                        'users': [{ 'name': 'onrack', 'password': 'Onr@ck1!', 'uid': 1010 }]
                    },
                    'set-boot-pxe': self.__obm_options,
                    'reboot': self.__obm_options,
                    'install-os': {
                        'schedulerOverrides': {
                            'timeout': 3600000
                        }
                    }
                }
            }
        self.__post_workflow(graph_name, nodes, body)  
        
    def install_suse(self, version, nodes=[], options=None):
        graph_name = 'Graph.InstallSUSE'
        os_repo = defaults.get('RACKHD_SUSE_REPO_PATH', \
            self.__base + '/repo/suse/{0}/'.format(version))
        body = options
        if body == None:
            body = {
                'options': {
                    'defaults': {
                        'installDisk': '/dev/sda',
                        'version': version,
                        'repo': os_repo,
                        'users': [{ 'name': 'onrack', 'password': 'Onr@ck1!', 'uid': 1010 }]
                    },
                    'set-boot-pxe': self.__obm_options,
                    'reboot': self.__obm_options,
                    'install-os': {
                        'schedulerOverrides': {
                            'timeout': 3600000
                        }
                    }
                }
            }
        self.__post_workflow(graph_name, nodes, body)
        
    def install_ubuntu(self, version, nodes=[], options=None):
        graph_name = 'Graph.InstallUbuntu'
        os_repo = defaults.get('RACKHD_UBUNTU_REPO_PATH', \
            self.__base + '/repo/ubuntu')
        body = options
        if body == None:
            body = {
                'options': {
                    'defaults': {
                        'installDisk': '/dev/sda',
                        'version': version,
                        'repo': os_repo,
                        'baseUrl':'install/netboot/ubuntu-installer/amd64',
                        'kargs':{
                            'live-installer/net-image': os_repo + '/install/filesystem.squashfs'
                        },
                        'users': [{ 'name': 'onrack', 'password': 'Onr@ck1!', 'uid': 1010 }],
                        'rootPassword': 'Onr@ck1!'
                    },
                    'set-boot-pxe': self.__obm_options,
                    'reboot': self.__obm_options,
                    'install-ubuntu': {
                        '_taskTimeout': 3600000
                    },
                    'validate-ssh': {
                        '_taskTimeout': 1200000,
                        'retries': 10
                    }
                }
            }
        self.__post_workflow(graph_name, nodes, body)
    
    def install_windowsServer2012(self, version, nodes=[], options=None):
        graph_name = 'Graph.InstallWindowsServer'
        os_repo = defaults.get('RACKHD_SMB_WINDOWS_REPO_PATH', None)
        if None == os_repo:
            fail('user must set RACKHD_SMB_WINDOWS_REPO_PATH')
        body = options
        if body == None:
            # The value of the productkey below is not a valid product key. It is a KMS client 
            # key that was generated to run the workflows without requiring a real product key. 
            # This key is available to public on the Microsoft site.
            body = {
                'options': {
                    'defaults': {
                        'productkey': 'D2N9P-3P6X9-2R39C-7RTCD-MDVJX',
                        'smbUser':  defaults.get('RACKHD_SMB_USER' , 'onrack'),
                        'smbPassword':  defaults.get('RACKHD_SMB_PASSWORD' , 'onrack'),
                        'completionUri': 'winpe-kickstart.ps1',
                        'smbRepo': os_repo,
                        'repo' : defaults.get('RACKHD_WINPE_REPO_PATH',  \
                            self.__base + '/repo/winpe')
                    },
                    'firstboot-callback-uri-wait':{
                        'completionUri': 'renasar-ansible.pub'
                    }
                }
            }
        self.__post_workflow(graph_name, nodes, body)

    def install_coreos(self, nodes=[], options=None):
        graph_name = 'Graph.InstallCoreOS'
        os_repo = defaults.get('RACKHD_COREOS_REPO_PATH', \
            self.__base + '/repo/coreos')
        body = options
        if body == None:
            body = self.__get_os_install_payload('install_coreos_payload_minimal.json', os_repo)
        self.__post_workflow(graph_name, nodes, body)

    @test(enabled=True, groups=['centos-6-5-install.v1.1.test'])
    def test_install_centos_6(self):
        """ Testing CentOS 6.5 Installer Workflow """
        self.install_centos('6.5')
        
    @test(enabled=True, groups=['centos-7-install.v1.1.test'])
    def test_install_centos_7(self, nodes=[], options=None):
        """ Testing CentOS 7 Installer Workflow """
        self.install_centos('7.0')

    @test(enabled=True, groups=['ubuntu-install.v1.1.test'])
    def test_install_ubuntu(self, nodes=[], options=None):
        """ Testing Ubuntu 14.04 Installer Workflow """
        self.install_ubuntu('trusty')
       
    @test(enabled=True, groups=['suse-install.v1.1.test'])
    def test_install_suse(self, nodes=[], options=None):
        """ Testing OpenSuse Leap 42.1 Installer Workflow """
        self.install_suse('42.1')
        
    @test(enabled=True, groups=['esxi-5-5-install.v1.1.test'])
    def test_install_esxi_5_5(self, nodes=[], options=None):
        """ Testing ESXi 5.5 Installer Workflow """
        self.install_esxi('5.5')
        
    @test(enabled=True, groups=['esxi-6-install.v1.1.test'])
    def test_install_esxi_6(self, nodes=[], options=None):
        """ Testing ESXi 6 Installer Workflow """
        self.install_esxi('6.0')
        
    @test(enabled=True, groups=['windowsServer2012-install.v1.1.test'])
    def test_install_windowsServer2012(self, nodes=[], options=None):
        """ Testing Windows Server 2012 Installer Workflow """
        self.install_windowsServer2012('10.40') 

    @test(enabled=True, groups=['coreos-install.v1.1.test'])
    def test_install_coreos(self, nodes=[], options=None):
        """ Testing CoreOS Installer Workflow """
        self.install_coreos()
