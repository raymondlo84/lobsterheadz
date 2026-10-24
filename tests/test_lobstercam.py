"""Exercise overlay selection without a webcam, display, or model inference."""

import contextlib
import io
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lobstercam


class OverlaySelectionTests(unittest.TestCase):
    def run_frame(self, image_path=None):
        camera = Mock()
        camera.isOpened.return_value = True
        camera.get.return_value = 30
        camera.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mesh = Mock()
        mesh.process.return_value = types.SimpleNamespace(multi_face_landmarks=[object()])
        argv = ["lobstercam.py"]
        if image_path is not None:
            argv += ["--image", str(image_path)]

        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(sys, "argv", argv))
            stack.enter_context(patch.object(cv2, "VideoCapture", return_value=camera))
            stack.enter_context(patch.object(lobstercam.mp_face, "FaceMesh", return_value=mesh))
            stack.enter_context(patch.object(lobstercam, "estimate_top_of_head", return_value=(320, 100, 0.2)))
            stack.enter_context(patch.object(lobstercam, "estimate_face_size", return_value=(0.3, 0.3)))
            draw = stack.enter_context(patch.object(lobstercam, "overlay_image_with_transparency", wraps=lobstercam.overlay_image_with_transparency))
            stack.enter_context(patch.object(cv2, "imshow"))
            stack.enter_context(patch.object(cv2, "waitKey", return_value=ord("q")))
            stack.enter_context(patch.object(cv2, "destroyAllWindows"))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            lobstercam.main()

        self.assertEqual(draw.call_count, 2)
        camera.release.assert_called_once()
        mesh.close.assert_called_once()
        return [call.args[1] for call in draw.call_args_list]

    def test_custom_image_reaches_both_render_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "green.png"
            image = np.full((32, 32, 4), [0, 255, 0, 255], dtype=np.uint8)
            self.assertTrue(cv2.imwrite(str(image_path), image))
            for actual in self.run_frame(image_path):
                np.testing.assert_array_equal(actual, image)

    def test_default_image_still_reaches_both_render_calls(self):
        expected = cv2.imread(lobstercam.LOBSTER_PATH, cv2.IMREAD_UNCHANGED)
        expected[expected[:, :, 3] == 0] = [255, 255, 255, 0]
        for actual in self.run_frame():
            np.testing.assert_array_equal(actual, expected)


if __name__ == "__main__":
    unittest.main()
