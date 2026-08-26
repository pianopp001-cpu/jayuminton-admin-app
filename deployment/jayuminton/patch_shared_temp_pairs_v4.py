# Final team contract: v4 intentionally delegates to v3.
# Permanent team: double line until explicit team release.
# Temporary game pair: selected two + automatic remaining two, separate solid overlays.
# Wait: pair A left column / pair B right column. Court: pair A top / pair B bottom.
# Team1/Team2 text is never rendered.
import runpy
runpy.run_path('deployment/jayuminton/patch_shared_temp_pairs_v3.py', run_name='__main__')
print('SHARED_TEMP_PAIRS_V4_OK final_2plus2=true wait=left-right court=top-bottom labels=none')
