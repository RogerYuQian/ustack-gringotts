from oslo.config import cfg

from gringotts import utils
from gringotts import constants as const

from gringotts.services import wrap_exception
from gringotts.services import Resource
from cinderclient.v1 import client as cinder_client
from gringotts.services import keystone as ks_client


class Volume(Resource):
    def to_message(self):
        msg = {
            'event_type': 'volume.create.end.again',
            'payload': {
                'volume_id': self.id,
                'display_name': self.name,
                'size': self.size,
                'user_id': self.user_id,
                'tenant_id': self.project_id
            },
            'timestamp': self.created_at
        }
        return msg


class Snapshot(Resource):
    def to_message(self):
        msg = {
            'event_type': 'snapshot.create.end.again',
            'payload': {
                'snapshot_id': self.id,
                'display_name': self.name,
                'volume_size': self.size,
                'user_id': self.user_id,
                'tenant_id': self.project_id
            },
            'timestamp': self.created_at
        }
        return msg


def get_cinderclient(region_name=None):
    os_cfg = cfg.CONF.service_credentials
    endpoint = ks_client.get_endpoint(region_name, 'volume')
    auth_token = ks_client.get_token()
    c = cinder_client.Client(os_cfg.os_username,
                             os_cfg.os_password,
                             None,
                             auth_url=os_cfg.os_auth_url)
    c.client.auth_token = auth_token
    c.client.management_url = endpoint
    return c


def volume_list(project_id, region_name=None, detailed=True, project_name=None):
    """To see all volumes in the cloud as admin.
    """
    c_client = get_cinderclient(region_name)
    search_opts = {'all_tenants': 1,
                   'project_id': project_id}
    if c_client is None:
        return []
    volumes = c_client.volumes.list(detailed, search_opts=search_opts)
    formatted_volumes = []
    for volume in volumes:
        created_at = utils.format_datetime(volume.created_at)
        status = utils.transform_status(volume.status)
        formatted_volumes.append(Volume(id=volume.id,
                                        name=volume.display_name,
                                        size=volume.size,
                                        status=status,
                                        original_status=volume.status,
                                        resource_type=const.RESOURCE_VOLUME,
                                        user_id = None,
                                        project_id = project_id,
                                        project_name=project_name,
                                        created_at=created_at))
    return formatted_volumes


def snapshot_list(project_id, region_name=None, detailed=True, project_name=None):
    """To see all snapshots in the cloud as admin
    """
    c_client = get_cinderclient(region_name)
    search_opts = {'all_tenants': 1,
                   'project_id': project_id}
    if c_client is None:
        return []
    snapshots = c_client.volume_snapshots.list(detailed, search_opts=search_opts)
    formatted_snap = []
    for sp in snapshots:
        created_at = utils.format_datetime(sp.created_at)
        status = utils.transform_status(sp.status)
        formatted_snap.append(Snapshot(id=sp.id,
                                       name=sp.display_name,
                                       size=sp.size,
                                       status=status,
                                       original_stauts=sp.status,
                                       resource_type=const.RESOURCE_SNAPSHOT,
                                       user_id=None,
                                       project_id=project_id,
                                       project_name=project_name,
                                       created_at=created_at))
    return formatted_snap


@wrap_exception(exc_type='bulk')
def delete_volumes(project_id, region_name=None):
    """Delete all volumes that belong to project_id
    """
    client = get_cinderclient(region_name)
    search_opts = {'all_tenants': 1,
                   'project_id': project_id}
    volumes = client.volumes.list(detailed=False, search_opts=search_opts)

    # Force delete or detach and then delete
    for volume in volumes:
        client.volumes.detach(volume)
        client.volumes.delete(volume)


@wrap_exception(exc_type='bulk')
def delete_snapshots(project_id, region_name=None):
    """Delete all snapshots that belong to project_id
    """
    client = get_cinderclient(region_name)
    search_opts = {'all_tenants': 1,
                   'project_id': project_id}
    snaps = client.volume_snapshots.list(detailed=False,
                                         search_opts=search_opts)

    for snap in snaps:
        client.volume_snapshots.delete(snap)


@wrap_exception()
def delete_volume(volume_id, region_name=None):
    client = get_cinderclient(region_name)
    client.volumes.detach(volume_id)
    client.volumes.delete(volume_id)

@wrap_exception()
def stop_volume(volume_id, region_name=None):
    return True

@wrap_exception()
def delete_snapshot(snap_id, region_name=None):
    client = get_cinderclient(region_name)
    client.volume_snapshots.delete(snap_id)

@wrap_exception()
def stop_snapshot(snap_id, region_id=None):
    return True