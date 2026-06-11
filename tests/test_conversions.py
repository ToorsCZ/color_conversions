from color_conversions import ncs_to_rgb, load_ral_colors, ral_to_rgb

def test_ncs_to_rgb():
    result = ncs_to_rgb("NCS S 0580-Y10R")
    assert result["r"] > 0
    assert result["g"] > 0
    assert result["b"] >= 0

def test_ral_to_rgb():
    ral_dict = load_ral_colors()
    rgb = ral_to_rgb("RAL 1000", ral_dict)
    assert len(rgb) == 3
    assert all(0 <= v <= 1 for v in rgb)
