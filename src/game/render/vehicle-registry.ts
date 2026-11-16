export const VEHICLES = [
  {
    "id": "volvo240",
    "name": "Volvo 240",
    "archetype": "volvo",
    "url": "media/vehicles/volvo240.glb",
    "radius": 0.315,
    "wheelbase": 2.65,
    "scale": 1,
    "forward": "-Z",
    "up": "+Y",
    "body": "body",
    "wheels": [
      "wheel_fl",
      "wheel_fr",
      "wheel_rl",
      "wheel_rr"
    ],
    "police": false,
    "source": "ff6a0f187add7bd9b7ba052f28bd0d67e534c33a",
    "master": "experiments/volvo240/refinement/model.blend"
  },
  {
    "id": "saab900",
    "name": "Saab 900 Classic",
    "archetype": "saab",
    "url": "media/vehicles/saab900-t16.glb",
    "radius": 0.305,
    "wheelbase": 2.517,
    "scale": 1,
    "forward": "-Z",
    "up": "+Y",
    "body": "body",
    "wheels": [
      "wheel_fl",
      "wheel_fr",
      "wheel_rl",
      "wheel_rr"
    ],
    "police": false,
    "source": "ff6a0f187add7bd9b7ba052f28bd0d67e534c33a",
    "master": "experiments/saab900/build/model.blend"
  },
  {
    "id": "xc70",
    "name": "Volvo XC70 P2",
    "archetype": "saab",
    "url": "media/vehicles/xc70-civilian.glb",
    "radius": 0.345,
    "wheelbase": 2.763,
    "scale": 1,
    "forward": "-Z",
    "up": "+Y",
    "body": "body",
    "wheels": [
      "wheel_fl",
      "wheel_fr",
      "wheel_rl",
      "wheel_rr"
    ],
    "police": false,
    "source": "ff6a0f187add7bd9b7ba052f28bd0d67e534c33a",
    "master": "experiments/xc70p2/build/model.blend"
  },
  {
    "id": "xc70-police",
    "name": "Police XC70 P2",
    "archetype": "polis",
    "url": "media/vehicles/xc70-police.glb",
    "radius": 0.345,
    "wheelbase": 2.763,
    "scale": 1,
    "forward": "-Z",
    "up": "+Y",
    "body": "body",
    "wheels": [
      "wheel_fl",
      "wheel_fr",
      "wheel_rl",
      "wheel_rr"
    ],
    "police": true,
    "source": "ff6a0f187add7bd9b7ba052f28bd0d67e534c33a",
    "master": "experiments/xc70p2/build/model.blend"
  },
  {
    "id": "impala1970",
    "name": "Chevrolet Impala 1970 hardtop",
    "archetype": "volvo",
    "url": "media/vehicles/impala1970.glb",
    "radius": 0.35,
    "wheelbase": 3.0226,
    "scale": 1,
    "forward": "-Z",
    "up": "+Y",
    "body": "body",
    "wheels": [
      "wheel_fl",
      "wheel_fr",
      "wheel_rl",
      "wheel_rr"
    ],
    "police": false,
    "source": "46fa31e9094ab6e1e30f2b542de83383f85fb7c7",
    "master": "experiments/impala1970/build/model.blend"
  },
  {
    "id": "micra-k11",
    "name": "Nissan Micra K11",
    "archetype": "saab",
    "url": "media/vehicles/micra-k11.glb",
    "radius": 0.276,
    "wheelbase": 2.36,
    "scale": 1,
    "forward": "-Z",
    "up": "+Y",
    "body": "body",
    "wheels": [
      "wheel_fl",
      "wheel_fr",
      "wheel_rl",
      "wheel_rr"
    ],
    "police": false,
    "source": "5c84a173f3bbd8206f067ec18594cecdaf5476b5",
    "master": "experiments/micra1995/build/model.blend"
  },
  {
    "id": "duett-epa",
    "name": "Volvo Duett P210 EPA",
    "archetype": "epa",
    "url": "media/vehicles/duett-p210-epa.glb",
    "radius": 0.335,
    "wheelbase": 2.6,
    "scale": 1,
    "forward": "-Z",
    "up": "+Y",
    "body": "body",
    "wheels": [
      "wheel_fl",
      "wheel_fr",
      "wheel_rl",
      "wheel_rr"
    ],
    "police": false,
    "source": "2be04e605ad20f9ffc5dbe097a493bd6a3991e6f",
    "master": "experiments/duettp210/build/model.blend"
  }
] as const;
export type VehicleId = typeof VEHICLES[number]["id"];
export const vehicleDefinition = (id: string | null) => VEHICLES.find(v => v.id === id);
