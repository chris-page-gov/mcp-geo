from scripts.landis_release_reconciliation import strip_html
from scripts.vendor_html_nojs import strip_scripts


def test_strip_html_removes_script_and_style_tags_with_space_before_close_angle() -> None:
    html = """
    <html>
      <head>
        <style type="text/css">body { color: red; }</style >
      </head>
      <body>
        keep me
        <script type="text/javascript">alert("nope")</script >
        <div>and me</div>
      </body>
    </html>
    """

    cleaned = strip_html(html)

    assert cleaned == "keep me and me"


def test_strip_html_removes_script_and_style_tags_with_text_before_close_angle() -> None:
    html = """
    <html>
      <head>
        <style type="text/css">body { color: red; }</style
          stray>
      </head>
      <body>
        keep me
        <script type="text/javascript">alert("nope")</script
          stray>
        <div>and me</div>
      </body>
    </html>
    """

    cleaned = strip_html(html)

    assert cleaned == "keep me and me"


def test_vendor_html_nojs_strip_scripts_handles_text_before_close_angle() -> None:
    html = """
    <body>
      keep me
      <script type="text/javascript">alert("nope")</script
        stray>
      <div>and me</div>
    </body>
    """

    cleaned = strip_scripts(html)

    assert '<script type="text/javascript">' not in cleaned
    assert 'alert("nope")' not in cleaned
    assert "keep me" in cleaned
    assert "and me" in cleaned
