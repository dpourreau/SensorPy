"""
C structure definitions for Sensirion sensors.
"""

from ctypes import Structure, c_float, c_uint8


class SPS30_Measurement(Structure):
    """
    Structure for holding SPS30 particulate matter measurement data.

    Units:
      - Mass concentrations (mc_*): in micrograms per cubic meter (µg/m³)
      - Number concentrations (nc_*): in counts per cubic centimeter (#/cm³)
      - Typical particle size: in micrometers (µm)
    """

    _fields_ = [
        ("mc_1p0", c_float),
        ("mc_2p5", c_float),
        ("mc_4p0", c_float),
        ("mc_10p0", c_float),
        ("nc_0p5", c_float),
        ("nc_1p0", c_float),
        ("nc_2p5", c_float),
        ("nc_4p0", c_float),
        ("nc_10p0", c_float),
        ("typical_particle_size", c_float),
    ]


class SPS30_VersionInfo(Structure):
    """
    Mirrors the struct sps30_version_information in C:

    struct sps30_version_information {
        uint8_t firmware_major;
        uint8_t firmware_minor;
        uint8_t hardware_revision;
        uint8_t shdlc_major;
        uint8_t shdlc_minor;
    };
    """

    _fields_ = [
        ("firmware_major", c_uint8),
        ("firmware_minor", c_uint8),
        ("hardware_revision", c_uint8),
        ("shdlc_major", c_uint8),
        ("shdlc_minor", c_uint8),
    ]
