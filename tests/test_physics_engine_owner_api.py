import numpy as np

from builtin.systems.physics_engine import PhysicsEngine


class OwnerBody:
    def __init__(self, position=(0.0, 0.0), velocity=(0.0, 0.0), acceleration=(0.0, 0.0)):
        self.position = np.asarray(position, dtype=float)
        self.velocity = np.asarray(velocity, dtype=float)
        self.acceleration = np.asarray(acceleration, dtype=float)
        self.calls: list[str] = []

    def set_position(self, value):
        self.calls.append("position")
        self.position = np.asarray(value, dtype=float)

    def set_velocity(self, value):
        self.calls.append("velocity")
        self.velocity = np.asarray(value, dtype=float)

    def set_acceleration(self, value):
        self.calls.append("acceleration")
        self.acceleration = np.asarray(value, dtype=float)


def test_physics_force_and_boundary_motion_use_owner_apis():
    body = OwnerBody(position=(9.0, 5.0), velocity=(5.0, 0.0))
    physics = PhysicsEngine(gravity=np.array([0.0, 0.0]), drag=1.0, world_size=(10.0, 10.0))

    physics.apply_force(body, np.array([1.0, 0.0]))
    physics.update_motion(body)

    assert body.calls == ["acceleration", "position", "velocity", "acceleration", "position", "velocity"]
    assert body.position.tolist() == [10.0, 5.0]
    assert np.allclose(body.velocity, [-4.8, 0.0])
    assert body.acceleration.tolist() == [0.0, 0.0]


def test_physics_rejects_malformed_force_without_mutating_owner_state():
    body = OwnerBody(acceleration=(2.0, 3.0))

    PhysicsEngine().apply_force(body, np.array([1.0, 2.0, 3.0]))

    assert body.calls == []
    assert body.acceleration.tolist() == [2.0, 3.0]



def test_collision_resolution_uses_owner_apis_for_separation_and_impulse():
    first = OwnerBody(position=(0.0, 0.0), velocity=(1.0, 0.0))
    second = OwnerBody(position=(15.0, 0.0), velocity=(-1.0, 0.0))
    physics = PhysicsEngine(collision_damping=0.8)

    physics.resolve_collision(first, second)

    assert first.calls == ["position", "velocity"]
    assert second.calls == ["position", "velocity"]
    assert np.allclose(first.position, [-22.5, 0.0])
    assert np.allclose(second.position, [37.5, 0.0])
    assert np.allclose(first.velocity, [-0.8, 0.0])
    assert np.allclose(second.velocity, [0.8, 0.0])
