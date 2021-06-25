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
import os
import tempfile

import sevenbridges as sbg
import synapseclient


def get_or_create_project(api, project_name):
   """Get or create a CAVATICA project

   Args:
      api: Synapse bridges connection
      project_name: Name of project

   Returns:
      CAVATICA Project

   """
   # pull out target project
   project = [p for p in api.projects.query(limit=100).all() \
              if p.name == project_name]

   if not project:
      print(f'Target project ({project_name}) not found, creating project')
      project = api.projects.create(name=project_name)
   else:
      project = project[0]
   return project


def copy_or_get_app(api, app_name, project):
   """Copy a public application if it doesnt exist in your project
   or get the existing public app

   Args:
      api: Seven bridges connection
      app_name: Name of public app
      project: CAVATICA project

   Returns:
      CAVATICA App
   """
   # Query all public application
   public_apps = api.apps.query(visibility='public').all()

   app = [public_app for public_app in public_apps
          if public_app.name == app_name][0]

   # Look for any duplicated application names in project
   project_apps = api.apps.query(project = project.id, limit=100)
   duplicate_app = [a for a in project_apps.all() if a.name == app.name]

   if duplicate_app:
      print('App already exists in second project, please try another app')
      copied_app = duplicate_app[0]
   else:
      # Copy the app if it doesn't exist
      print(f'App ({app_name}) does not exist in '
            f'Project ({project.name}); copying now')
      copied_app = app.copy(project = project.id, name = app_name)

      # re-list apps in target project to verify the copy worked
      my_apps = api.apps.query(project = project.id, limit=100)
      my_app_names = [a.name for a in my_apps.all()]

      if app_name in my_app_names:
         print('Sucessfully copied one app!')
      else:
         print('Something went wrong...')
   return copied_app


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

   project = get_or_create_project(api=api, project_name=project_name)

   # Copy an application to your CAVATICA project
   # https://github.com/sbg/okAPI/blob/d3bcdeca309534603ae715cf2646c5f65e89d98f/Recipes/CGC/apps_copyFromPublicApps.ipynb
   copied_app = copy_or_get_app(api=api, app_name=app_name, project=project)

   # Add step to download some fastq files from Synapse
   syn = synapseclient.login()
   read1 = syn.get("syn11223576")
   read2 = syn.get("syn11223563")
   # And upload to CAVATICA
   api.files.upload(path=read1.path, project=project.id)
   api.files.upload(path=read2.path, project=project.id)

   print(copied_app)
   # Hard coded
   sample_id = "C9DL6ANXX"
   sample_files = api.files.query(project=project.id)
                                  #metadata={'sample_id': sample_id})
   fastq_files = [sample_file for sample_file in sample_files
                  if sample_file.name in [os.path.basename(read1.name), os.path.basename(read2.name)]]
   inputs = {
      "output_basename": "test",
      "sample_name": sample_id,
      "runThread": 1,
      "input_type": "FASTQ",
      "STAR_outSAMattrRGline": "ID:sample_name\tLB:aliquot_id\tPL:platform\tSM:BSID",
      "wf_strand_param": "default",
      "reads1": fastq_files[0],
      "reads2": fastq_files[1]
   }
   # TODO: Missing rest call that automatically copies
   # reference files?
   task = api.tasks.create(name="trial_run",
                           project=project.id, app=copied_app.id,
                           inputs=inputs,
                           run=True)

   # Hard coded task for now
   task_id = task.id
   task = api.tasks.get(task_id)
   task_outputs = task.outputs
   # Download outputs except for bam files (large)
   temp_dir = tempfile.TemporaryDirectory()
   output_files = []
   for _, output_value in task_outputs.items():
      if output_value is not None:
         if not output_value.name.endswith(".bam"):
            output_file = api.files.get(output_value.id)
            output_path = os.path.join(temp_dir.name, output_value.name)
            output_file.download(output_path)
            output_files.append(output_path)

   # Store output files into synapse
   synapse_project = "syn25920979"
   synapse_task_folder = syn.store(
      synapseclient.Folder(name=task_id, parent=synapse_project)
   )
   # Unfortunately no recursive store function currently...
   for output_file in output_files:
      syn.store(
         synapseclient.File(path=output_file, parent=synapse_task_folder)
      )
   temp_dir.cleanup()
