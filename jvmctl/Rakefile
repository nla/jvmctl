ROOT = File.dirname(__FILE__)
SPECFILE = File.join(ROOT, 'jvmctl.spec')

require 'rake/version_task'
Rake::VersionTask.new do |task|
  task.with_git_tag = false
end

desc "Download source archive as specified in the specfile"
task :fetch do |task|
  source_archive = IO.popen("/usr/bin/spectool #{SPECFILE}").read.match(/Source0: (.*)/)[1]

  Dir.chdir(File.join(ENV['HOME'], 'rpmbuild', 'SOURCES')) do
    system '/usr/bin/wget', source_archive
  end
end

desc "Clean up generated artifacts"
task :clean do |task|
  require 'fileutils'
  include FileUtils

  rm_r File.join(ROOT, 'RPMS')
end

desc "Generate an RPM for EL"
task :build do |task|
  require 'fileutils'
  include FileUtils

  dir = File.dirname(__FILE__)

  version = File.read(File.join(ROOT, 'VERSION')).chomp
  release = File.read(SPECFILE).match(/Release: (.*)/)[1]

  system 'rpmbuild', '-bb', SPECFILE

  mkdir_p 'RPMS'
  cp File.join(ENV['HOME'], 'rpmbuild', 'RPMS', 'noarch', "jvmctl-#{version}-#{release}.noarch.rpm"), 'RPMS'
end

task :build => :fetch

desc "Push the contents of ./RPMS to SPACEWALK_CHANNEL on SPACEWALK_SERVER"
task :push do |task|
  abort("No RPM dir found") unless File.exist?(File.join(ROOT, 'RPMS'))
  if ENV['SPACEWALK_USER'].nil?
    abort("Required environment variable SPACEWALK_USER not set")
  end

  if ENV['SPACEWALK_PASS'].nil?
    abort("Required environment variable SPACEWALK_PASS not set")
  end

  if ENV['SPACEWALK_CHANNEL'].nil?
    abort("Required environment variable SPACEWALK_CHANNEL not set")
  end

  if ENV['SPACEWALK_SERVER'].nil?
    abort("Required environment variable SPACEWALK_SERVEL not set")
  end
  system '/usr/bin/rhnpush', '-v',
    '-u', ENV['SPACEWALK_USER'],
    '-p', ENV['SPACEWALK_PASS'],
    sprintf('--channel=%s', ENV['SPACEWALK_CHANNEL']),
    sprintf('--server=%s', ENV['SPACEWALK_SERVER']),
    sprintf('--dir=%s', File.join(ROOT, 'RPMS')),
    '--nosig'
end


