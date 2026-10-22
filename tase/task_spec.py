"""Native scene binding. Authorization is separate from policy instruction."""
from dataclasses import dataclass


@dataclass
class TaskSpec:
    target: str
    basket: str
    objects: dict
    left_geoms: list
    right_geoms: list

    def validate(self):
        if self.target == self.basket or not {self.target, self.basket} <= set(self.objects):
            raise ValueError('missing/conflicting authorized target or basket')
        if not self.left_geoms or not self.right_geoms or set(self.left_geoms)&set(self.right_geoms):
            raise ValueError('missing/overlapping finger contact geometry')
        seen=set()
        bodies=set();body_names=set()
        for name, item in self.objects.items():
            if (type(item.get('body_id')) is not int or item['body_id']<=0 or
                    not item.get('body_name') or item['body_id'] in bodies or item['body_name'] in body_names):
                raise ValueError('missing/duplicate object body: '+name)
            if (not item['geoms'] or len(item['geoms'])!=len(set(item['geoms'])) or
                    seen&set(item['geoms']) or any(type(g) is not int or g<0 for g in item['geoms']) or
                    len(item.get('geom_names',[]))!=len(item['geoms']) or
                    len(set(item['geom_names']))!=len(item['geoms'])):
                raise ValueError('missing/overlapping object geometry: '+name)
            seen.update(item['geoms'])
            bodies.add(item['body_id']);body_names.add(item['body_name'])
        if seen & (set(self.left_geoms)|set(self.right_geoms)):
            raise ValueError('object geometry overlaps robot')
        return self

    @classmethod
    def from_native(cls, raw, task):
        env=raw.env; model=raw.sim.model
        objects={}
        for name, obj in env.objects_dict.items():
            objects[name]={'body_name':obj.root_body,'body_id':model.body_name2id(obj.root_body),
                           'geom_names':list(obj.contact_geoms),
                           'geoms':[model.geom_name2id(g) for g in obj.contact_geoms]}
        grip=raw.robots[0].gripper.important_geoms
        # Native robosuite's grasp check uses the same two pad groups.
        left=grip['left_fingerpad'];right=grip['right_fingerpad']
        spec=cls(task+'_1','basket_1',objects,
                 [model.geom_name2id(g) for g in left],
                 [model.geom_name2id(g) for g in right])
        return spec.validate()
