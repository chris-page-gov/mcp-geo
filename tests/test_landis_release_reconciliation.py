from scripts.landis_release_reconciliation import strip_html


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
