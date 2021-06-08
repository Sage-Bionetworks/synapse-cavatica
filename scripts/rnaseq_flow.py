"""
This is a a proof-of-concept flow for some RNA-seq data using this
KF RNA-Seq workflow: https://github.com/kids-first/kf-rnaseq-workflow
Link on CAVATICA: https://cavatica.sbgenomics.com/public/apps#cavatica/apps-publisher/kfdrc-rnaseq-workflow/

Here are the high level steps:

1. RNA-seq data files [FASTQ] and metadata [annotations/CSV] indexed in
   Synapse, stored in S3
2. Manual submission that couples synapseclient and CAVATICA API
3. Semi-automated submission using Synapse Evaluation API or AWS Lambda
4. Execution of processing workflow [CWL] in CAVATICA environment
    - if there should be status updates back to Synapse
      (e.g. 58% of processing is done)
4. Return of results [BAMs, TSVs] to Synapse, or elsewhere.

More details of this task can be found here:
https://github.com/include-dcc/stwg-issue-tracking/issues/7
"""
import sevenbridges as sbg
import synapseclient


def get_or_create_project(api, project_name):
   """Get or create a CAVATICA project"""
   # pull out target project
   project = [p for p in api.projects.query(limit=100).all() \
              if p.name == project_name]

   if not project:
      print(f'Target project ({project_name}) not found, creating project')
      project = api.projects.create(name=project_name)
   else:
      project = project[0]
   return project


def _sbg_paginated_query(query_func, limit=100, offset=0, **kwargs):
   """Seven bridges paginated queries"""
   # Get inital results
   collection = query_func(limit=limit, offset=offset, **kwargs)

   while collection.total > (limit + offset):
      collection = query_func(limit=limit, offset=offset, **kwargs)
      offset += limit
      # Yield all results in collections
      for result in collection:
         yield result


def main():
   # Setup Seven bridges API
   # https://github.com/sbg/okAPI/blob/a6c0816235ae8742913950d38cc5f57b5ab6314e/Recipes/CGC/Setup_API_environment.ipynb
   # Pull credential from ~/.sevenbridges/credentials
   config_file = sbg.Config(profile='cavatica')
   api = sbg.Api(config=config_file)

   # CAVATICA project name
   project_name = "Test"
   # Public CAVATIC app-rnaseq workflow
   app_name = "Kids First DRC RNAseq Workflow"

   project = get_or_create_project(api, project_name)

   # Copy an application to your CAVATICA project
   # https://github.com/sbg/okAPI/blob/d3bcdeca309534603ae715cf2646c5f65e89d98f/Recipes/CGC/apps_copyFromPublicApps.ipynb

   # Query all public application
   public_apps = _sbg_paginated_query(query_func=api.apps.query, visibility='public')

   app = [public_app for public_app in public_apps
          if public_app.name == app_name][0]

   # Look for any duplicated application names in project
   project_apps = api.apps.query(project = project.id, limit=100)
   duplicate_app = [a for a in project_apps.all() if a.name == app.name]

   if duplicate_app:
      print('App already exists in second project, please try another app')
   else:
      #  Copy the app if it doesn't exist
      print(f'App ({app_name}) does not exist in '
            f'Project ({project_name}); copying now')
      copied_app = app.copy(project = project.id, name = app_name)

      # re-list apps in target project to verify the copy worked
      my_apps = api.apps.query(project = project.id, limit=100)
      my_app_names = [a.name for a in my_apps.all()]

      if app_name in my_app_names:
         print('Sucessfully copied one app!')
      else:
         print('Something went wrong...')
